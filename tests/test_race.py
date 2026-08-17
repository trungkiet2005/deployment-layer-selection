"""Correctness of the exact interaction-layer computation."""

from __future__ import annotations

import numpy as np
import pytest

from dls.race import (
    SAFE,
    STRATEGIES,
    UNSAFE,
    RaceParams,
    action_paths,
    build_race_tables,
    evaluate_matchup,
)


def test_horizon_distribution_is_a_probability_measure():
    params = RaceParams()
    t_values, probs = params.horizon_distribution()
    assert t_values[0] == params.min_rounds
    assert probs.min() >= 0.0
    assert probs.sum() == pytest.approx(1.0, abs=1e-15)
    assert params.expected_horizon == pytest.approx(9.0, abs=1e-9)


def test_conditional_strategies_follow_their_definition():
    a_row, a_col = action_paths("CAS", "AS", 5)
    assert list(a_row) == [UNSAFE, SAFE, SAFE, SAFE, SAFE]
    assert list(a_col) == [SAFE] * 5

    a_row, a_col = action_paths("CS", "CAS", 5)
    assert list(a_row) == [SAFE, UNSAFE, SAFE, UNSAFE, SAFE]
    assert list(a_col) == [UNSAFE, SAFE, UNSAFE, SAFE, UNSAFE]

    a_row, a_col = action_paths("CAS", "CAS", 4)
    assert list(a_row) == [UNSAFE] * 4
    assert list(a_col) == [UNSAFE] * 4


def test_always_safe_self_play_matches_closed_form():
    params = RaceParams(p_max=0.6)
    out = evaluate_matchup("AS", "AS", params)
    # both players tie, split the prize, and take no risk
    expected = params.expected_horizon * 1.0 + params.prize / 2.0
    assert out.payoff == pytest.approx(expected, rel=1e-9)
    assert out.unsafe_count == 0.0
    assert out.tie_probability == pytest.approx(1.0)


def test_always_unsafe_self_play_matches_closed_form():
    params = RaceParams(p_max=0.6)
    out = evaluate_matchup("AU", "AU", params)
    kept = params.expected_horizon * 2.0 + params.prize / 2.0
    assert out.payoff == pytest.approx((1.0 - params.p_max) * kept, rel=1e-9)
    assert out.unsafe_frequency == pytest.approx(1.0)
    assert out.setback_probability == pytest.approx(params.p_max)


def test_monte_carlo_agrees_with_the_exact_evaluation():
    """The exact horizon average reproduces a direct simulation of the race."""
    params = RaceParams(p_max=0.6)
    rng = np.random.default_rng(0)
    n_draws = 200_000
    horizons = params.min_rounds + rng.geometric(params.stop_prob, n_draws) - 1

    for row, col in [("CAS", "CS"), ("CS", "CAS"), ("AU", "CS"), ("CAS", "AS")]:
        exact = evaluate_matchup(row, col, params)
        n = int(horizons.max())
        a_row, a_col = action_paths(row, col, n)
        stage = np.cumsum(params.stage_payoffs[a_row, a_col])
        steps = np.cumsum(np.where(a_row == UNSAFE, params.step_unsafe, params.step_safe))
        steps_o = np.cumsum(np.where(a_col == UNSAFE, params.step_unsafe, params.step_safe))
        n_unsafe = np.cumsum(a_row == UNSAFE)

        idx = horizons - 1
        q = params.p_max * n_unsafe[idx] / horizons
        wins = steps[idx] > steps_o[idx]
        ties = steps[idx] == steps_o[idx]
        prize = np.where(wins, params.prize, 0.0) + np.where(ties, params.prize / 2, 0.0)
        kept = stage[idx] + prize
        setback = rng.random(n_draws) < q
        payoff = np.where(wins | ties, np.where(setback, 0.0, kept), stage[idx])

        assert payoff.mean() == pytest.approx(exact.payoff, rel=0.02)
        assert n_unsafe[idx].mean() == pytest.approx(exact.unsafe_count, rel=0.02)


def test_tables_are_consistent_across_treatments():
    for p_max in (0.1, 0.6, 0.9):
        tables = build_race_tables(RaceParams(p_max=p_max))
        assert tables.payoff.shape == (len(STRATEGIES), len(STRATEGIES))
        assert np.all(tables.unsafe_count >= 0)
        assert np.all(tables.unsafe_frequency >= 0)
        assert np.all(tables.unsafe_frequency <= 1 + 1e-12)
        # the private risk treatment cannot change the action paths
        assert np.allclose(tables.unsafe_count, build_race_tables(
            RaceParams(p_max=0.1)).unsafe_count)


def test_subset_preserves_entries():
    tables = build_race_tables(RaceParams(p_max=0.6))
    sub = tables.subset(("AS", "CAS"))
    assert sub.strategies == ("AS", "CAS")
    i, j = STRATEGIES.index("AS"), STRATEGIES.index("CAS")
    assert sub.payoff[0, 1] == pytest.approx(tables.payoff[i, j])
    assert sub.unsafe_count[1, 0] == pytest.approx(tables.unsafe_count[j, i])
