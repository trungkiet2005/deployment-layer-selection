"""The structural results must hold exactly, not approximately."""

from __future__ import annotations

import numpy as np
import pytest

from dls.dynamics import (
    average_replicator_attractor,
    integrate_replicator,
    neutrally_stable_strategies,
    replicator_field,
)
from dls.functionals import (
    build_functionals,
    build_selection_matrix,
    is_column_constant,
    strategic_distortion,
)
from dls.race import RaceParams, build_race_tables
from dls.theory import (
    attractor_unsafe_values,
    bistability_window_exact,
    critical_cs_fraction,
    evaluation_filter,
    face_equilibrium,
    guard_invasion_threshold,
    invades_face_equilibrium,
    invasion_threshold,
    longrun_unsafe_replicator,
    matched_longrun_unsafe,
    safe_face_barrier,
    safe_face_is_neutral,
    solo_evaluation_scores,
)

BASE = build_race_tables(RaceParams(p_max=0.6))
POOL3 = ("AS", "CS", "CAS")


# --------------------------------------------------------------------------
# the wedge
# --------------------------------------------------------------------------


def test_dynamics_depend_only_on_the_product_lambda_times_harm():
    a = build_functionals(BASE, lam=0.5, harm=8.0).pi_P
    b = build_functionals(BASE, lam=0.2, harm=20.0).pi_P
    assert np.allclose(a, b)


def test_wedge_is_strategically_inert_only_at_full_liability():
    for lam in (0.0, 0.3, 0.7, 0.99):
        wedge = build_functionals(BASE, lam=lam, harm=10.0).wedge
        assert not is_column_constant(wedge)
        assert strategic_distortion(wedge) > 0
    wedge = build_functionals(BASE, lam=1.0, harm=10.0).wedge
    assert is_column_constant(wedge)
    assert strategic_distortion(wedge) == pytest.approx(0.0, abs=1e-12)


def test_column_constant_perturbation_leaves_the_replicator_field_unchanged():
    rng = np.random.default_rng(3)
    payoff = build_selection_matrix(BASE, 5.0)
    perturbed = payoff + np.ones((4, 1)) @ rng.normal(size=(1, 4))
    for _ in range(20):
        x = rng.dirichlet(np.ones(4))
        assert np.allclose(replicator_field(x, payoff), replicator_field(x, perturbed))


# --------------------------------------------------------------------------
# invasion thresholds
# --------------------------------------------------------------------------


def test_invasion_thresholds_match_a_direct_payoff_comparison():
    for invader in BASE.strategies:
        for resident in BASE.strategies:
            if invader == resident:
                continue
            th = invasion_threshold(BASE, invader, resident)
            i = BASE.strategies.index(invader)
            j = BASE.strategies.index(resident)
            for L in (0.0, 0.3, 1.0, 5.0, 43.0, 100.0):
                m = build_selection_matrix(BASE, L)
                direct = m[i, j] > m[j, j] + 1e-9
                assert th.invades_at(L) == direct, (invader, resident, L)


def test_safe_face_is_exactly_neutral():
    assert safe_face_is_neutral(BASE)
    for L in (0.0, 1.0, 50.0):
        m = build_selection_matrix(BASE, L)
        i, j = BASE.strategies.index("AS"), BASE.strategies.index("CS")
        assert m[i, i] == pytest.approx(m[j, i])
        assert m[i, j] == pytest.approx(m[j, j])


def test_conditional_safety_raises_the_invasion_barrier_by_two_orders():
    barrier_as = safe_face_barrier(BASE, 0.0)
    barrier_cs = safe_face_barrier(BASE, 1.0)
    assert barrier_as == pytest.approx(
        invasion_threshold(BASE, "CAS", "AS").critical_liability
    )
    assert barrier_cs == pytest.approx(
        invasion_threshold(BASE, "CAS", "CS").critical_liability
    )
    assert barrier_as / barrier_cs > 70.0
    xs = np.linspace(0, 1, 50)
    barriers = [safe_face_barrier(BASE, x) for x in xs]
    assert all(np.diff(barriers) < 0)


def test_critical_cs_fraction_is_consistent_with_the_barrier():
    for L in (1.0, 3.0, 10.0, 30.0):
        x = critical_cs_fraction(BASE, L)
        assert safe_face_barrier(BASE, min(x + 1e-4, 1.0)) <= L + 1e-6
        if x > 1e-4:
            assert safe_face_barrier(BASE, x - 1e-4) >= L - 1e-6


# --------------------------------------------------------------------------
# solo evaluation filters
# --------------------------------------------------------------------------


def test_a_solo_evaluation_cannot_distinguish_CAS_from_a_safe_design():
    scores = solo_evaluation_scores(BASE)
    assert scores["AS"] == 0.0
    assert scores["CS"] == 0.0
    assert scores["AU"] == pytest.approx(1.0)
    # CAS defects exactly once, so its solo score decays like 1 / E[T]
    assert 0.0 < scores["CAS"] < 0.2
    assert evaluation_filter(BASE, 0.2) == ("AS", "CS", "CAS")
    assert "AU" not in evaluation_filter(BASE, 0.2)


def test_CAS_weakly_dominates_AU_at_every_liability():
    i, j = BASE.strategies.index("CAS"), BASE.strategies.index("AU")
    for L in (0.0, 0.3, 1.0, 5.0, 42.0, 200.0):
        m = build_selection_matrix(BASE, L)
        assert np.all(m[i] >= m[j] - 1e-12)
        for k in ("AS", "CS"):
            c = BASE.strategies.index(k)
            assert m[i, c] > m[j, c] + 1e-9
        for k in ("AU", "CAS"):
            c = BASE.strategies.index(k)
            assert m[i, c] == pytest.approx(m[j, c])


def test_the_dominated_design_cannot_gain_ground_on_its_conditional_twin():
    """Weak dominance makes x_AU / x_CAS non-increasing along every solution."""
    full = evaluation_filter(BASE, 1.0)
    sub = BASE.subset(full)
    i, j = full.index("AU"), full.index("CAS")
    for L in (0.0, 0.3, 5.0):
        _, traj = integrate_replicator(
            build_selection_matrix(sub, L),
            np.array([0.25, 0.25, 0.25, 0.25]), t_end=400.0, n_points=400,
        )
        ratio = traj[:, i] / np.maximum(traj[:, j], 1e-300)
        assert np.all(np.diff(ratio) <= 1e-9)


def test_filtering_removes_only_the_all_unsafe_attractor():
    """Removing AU can delete an attractor, but never one with lower harm."""
    full = evaluation_filter(BASE, 1.0)
    filtered = evaluation_filter(BASE, 0.2)
    for L in (0.0, 0.05, 0.3, 3.0, 10.0):
        a = attractor_unsafe_values(BASE, L, pool=full, n_starts=80)
        b = attractor_unsafe_values(BASE, L, pool=filtered, n_starts=80)
        extra = a - b
        assert all(v >= max(b) - 1e-9 for v in extra), (L, a, b)


def test_filtering_does_not_change_the_outcome_under_a_matched_start_measure():
    full = evaluation_filter(BASE, 1.0)
    filtered = evaluation_filter(BASE, 0.2)
    for L in (0.0, 0.05, 0.3, 3.0, 10.0):
        u_full = matched_longrun_unsafe(BASE, L, pool=full, n_starts=60)
        u_filtered = matched_longrun_unsafe(BASE, L, pool=filtered, n_starts=60)
        assert u_filtered == pytest.approx(u_full, abs=0.02)


# --------------------------------------------------------------------------
# face equilibria, bistability and the liability valley
# --------------------------------------------------------------------------


def test_face_equilibrium_is_a_rest_point_of_the_face():
    for L in (3.0, 5.0, 10.0, 30.0):
        eq = face_equilibrium(BASE, "AS", "CAS", L)
        assert eq.fraction_second is not None
        sub = BASE.subset(("AS", "CAS"))
        x = np.array([1 - eq.fraction_second, eq.fraction_second])
        field = replicator_field(x, build_selection_matrix(sub, L))
        assert np.allclose(field, 0.0, atol=1e-10)


def test_guard_invasion_of_the_unsafe_face_does_not_depend_on_the_mixture():
    threshold = guard_invasion_threshold(BASE)
    for L in (2.5, 3.5, 4.0, 4.5, 6.0, 20.0):
        eq = face_equilibrium(BASE, "AS", "CAS", L)
        if eq.fraction_second is None:
            continue
        assert invades_face_equilibrium(BASE, "CS", "AS", "CAS", L) == (L < threshold)


def test_bistability_window_is_non_empty_and_matches_the_numerics():
    window = bistability_window_exact(BASE)
    assert window is not None
    lo, hi = window
    assert 0 < lo < hi
    below = longrun_unsafe_replicator(BASE, lo * 0.95, pool=POOL3, n_starts=80)
    inside = longrun_unsafe_replicator(BASE, lo * 1.05, pool=POOL3, n_starts=80)
    above = longrun_unsafe_replicator(BASE, hi * 1.05, pool=POOL3, n_starts=80)
    assert below == pytest.approx(0.0, abs=1e-6)
    assert inside > 0.1
    assert above == pytest.approx(0.0, abs=1e-6)


def test_long_run_harm_is_not_monotone_in_the_liability():
    """Raising liability across the valley edge strictly increases harm."""
    window = bistability_window_exact(BASE)
    assert window is not None
    lo, _ = window
    before = longrun_unsafe_replicator(BASE, lo * 0.9, pool=POOL3, n_starts=120)
    after = longrun_unsafe_replicator(BASE, lo * 1.1, pool=POOL3, n_starts=120)
    assert after > before + 0.1


# --------------------------------------------------------------------------
# integration sanity
# --------------------------------------------------------------------------


def test_replicator_trajectories_stay_on_the_simplex():
    payoff = build_selection_matrix(BASE, 5.0)
    _, traj = integrate_replicator(payoff, np.array([0.3, 0.2, 0.4, 0.1]), t_end=500.0)
    assert np.all(traj >= -1e-12)
    assert np.allclose(traj.sum(axis=1), 1.0)


def test_high_liability_removes_unsafe_designs_from_the_attractor():
    x = average_replicator_attractor(build_selection_matrix(BASE, 60.0), n_starts=40)
    assert x[BASE.strategies.index("AU")] < 1e-6
    assert x[BASE.strategies.index("CAS")] < 1e-6
    m = build_selection_matrix(BASE, 60.0)
    nss = [BASE.strategies[i] for i in neutrally_stable_strategies(m)]
    assert set(nss) <= {"AS", "CS"}
