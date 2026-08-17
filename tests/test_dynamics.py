"""Finite-population machinery and the eco-evolutionary ratchet."""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from dls.dynamics import (
    replicator_mutator_field,
    sparse_stationary_distribution,
    stationary_analysis,
    stationary_analysis_sml,
)
from dls.functionals import build_selection_matrix
from dls.race import RaceParams, build_race_tables
from dls.ratchet import RatchetParams, hysteresis_sweep, integrate_coupled
from dls.theory import invasion_threshold

BASE = build_race_tables(RaceParams(p_max=0.6))
POOL3 = ("AS", "CS", "CAS")


def test_sparse_stationary_distribution_matches_a_known_chain():
    p = np.array([[0.9, 0.1, 0.0], [0.2, 0.5, 0.3], [0.0, 0.4, 0.6]])
    pi = sparse_stationary_distribution(sp.csr_matrix(p))
    assert pi.sum() == pytest.approx(1.0)
    assert np.allclose(pi @ p, pi, atol=1e-12)


def test_replicator_mutator_keeps_the_state_in_the_interior():
    payoff = build_selection_matrix(BASE, 0.0)
    x = np.array([1.0 - 3e-9, 1e-9, 1e-9, 1e-9])
    field = replicator_mutator_field(x, payoff, mutation=1e-3)
    assert field[1] > 0 and field[2] > 0 and field[3] > 0
    assert field.sum() == pytest.approx(0.0, abs=1e-12)


def test_stationary_distribution_is_a_probability_vector():
    sub = BASE.subset(POOL3)
    res = stationary_analysis(
        build_selection_matrix(sub, 3.0), sub.unsafe_frequency,
        population_size=30, beta=0.05, mu=0.02,
    )
    assert res.state_distribution.sum() == pytest.approx(1.0, abs=1e-9)
    assert res.strategy_frequencies.sum() == pytest.approx(1.0, abs=1e-9)
    assert 0.0 <= res.unsafe_frequency <= 1.0


def test_small_mutation_limit_approximates_the_full_chain():
    sub = BASE.subset(POOL3)
    for L in (0.0, 20.0):
        pi_p = build_selection_matrix(sub, L)
        full = stationary_analysis(
            pi_p, sub.unsafe_frequency, population_size=50, beta=0.05, mu=1e-3
        )
        sml = stationary_analysis_sml(
            pi_p, sub.unsafe_frequency, population_size=50, beta=0.05
        )
        assert sml.unsafe_frequency == pytest.approx(full.unsafe_frequency, abs=0.12)


def test_liability_reduces_stationary_unsafe_frequency_in_the_small_mutation_limit():
    sub = BASE.subset(POOL3)
    values = [
        stationary_analysis_sml(
            build_selection_matrix(sub, L), sub.unsafe_frequency,
            population_size=50, beta=0.05,
        ).unsafe_frequency
        for L in (0.0, 0.3, 1.0, 5.0, 50.0)
    ]
    assert all(b <= a + 1e-9 for a, b in zip(values, values[1:]))


def test_the_ratchet_variable_never_decreases():
    sub = BASE.subset(POOL3)
    params = RatchetParams(theta=0.9, epsilon=0.05, mutation=1e-6)
    _, states = integrate_coupled(
        sub, 0.1, params, np.array([0.3, 0.4, 0.3]), z0=0.0, t_end=800.0, n_points=200
    )
    z = states[:, -1]
    assert np.all(np.diff(z) >= -1e-9)  # solver tolerance, not a real decrease
    assert z[-1] > z[0]


def test_hysteresis_loop_width_matches_the_erosion_parameter():
    """The recovery threshold is the loss threshold divided by ``1 - theta``."""
    sub = BASE.subset(POOL3)
    theta = 0.9
    params = RatchetParams(theta=theta, epsilon=0.05, mutation=1e-6)
    grid = np.geomspace(0.12, 25.0, 60)
    sweep = hysteresis_sweep(
        sub, params, grid, x0=np.array([0.02, 0.96, 0.02]), t_end=3000.0
    )
    assert sweep.loop_area > 0.5

    # the protected regime is the one with U ~ 0; the transition on the
    # ascending branch passes through a coexistence range, so recovery is the
    # last liability at which the population is still not protected
    l_star = invasion_threshold(BASE, "CAS", "CS").critical_liability
    assert l_star is not None
    down = grid[np.flatnonzero(sweep.unsafe_forward > 0.01)[-1]]
    up = grid[np.flatnonzero(sweep.unsafe_backward > 0.01)[-1]]
    assert down == pytest.approx(l_star, rel=0.25)
    assert up == pytest.approx(l_star / (1 - theta), rel=0.25)
    assert up > down * 4.0
