"""Tests for the round-4 extensions: measurement channel, assortment, grim."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from dls import RaceParams, build_race_tables
from dls.assortment import (
    assort_matrix,
    assorted_tables,
    assortment_thresholds,
    closing_assortment,
)
from dls.dynamics import replicator_attractor, replicator_field
from dls.functionals import build_selection_matrix, is_column_constant
from dls.noisy import REDUCED_DESIGNS, build_noisy_tables, grim
from dls.observation import (
    MeasurementModel,
    attribution_thresholds,
    delayed_replicator,
    measured_tables,
    measurement_is_inert,
)
from dls.theory import (
    guard_invasion_threshold,
    invasion_threshold,
    safe_face_barrier,
    safe_face_is_neutral,
)


@pytest.fixture(scope="module")
def base():
    return build_race_tables(RaceParams())


# --------------------------------------------------------------------------
# the measurement channel: three inert terms and one that is not
# --------------------------------------------------------------------------


def test_offset_is_column_constant_and_inert(base):
    model = MeasurementModel(offset=7.5)
    assert measurement_is_inert(base, model)
    charged = measured_tables(base, model)
    delta = charged.unsafe_count - base.unsafe_count
    assert is_column_constant(delta)
    assert guard_invasion_threshold(charged) == pytest.approx(
        guard_invasion_threshold(base), rel=1e-12
    )
    for invader, resident in (("CAS", "AS"), ("CAS", "CS"), ("CS", "CAS")):
        a = invasion_threshold(charged, invader, resident).critical_liability
        b = invasion_threshold(base, invader, resident).critical_liability
        assert a == pytest.approx(b, rel=1e-12)


def test_offset_leaves_the_replicator_field_unchanged(base):
    charged = measured_tables(base, MeasurementModel(offset=2.0))
    x = np.array([0.3, 0.1, 0.25, 0.35])
    for liability in (0.0, 5.0, 40.0):
        f_base = replicator_field(x, build_selection_matrix(base, liability))
        f_meas = replicator_field(x, build_selection_matrix(charged, liability))
        assert np.allclose(f_base, f_meas, atol=1e-12)


def test_gain_rescales_the_liability_axis_exactly(base):
    for alpha in (0.25, 0.5, 2.0):
        charged = measured_tables(base, MeasurementModel(gain=alpha))
        assert guard_invasion_threshold(charged) == pytest.approx(
            guard_invasion_threshold(base) / alpha, rel=1e-12
        )
        assert invasion_threshold(
            charged, "CAS", "AS"
        ).critical_liability == pytest.approx(
            invasion_threshold(base, "CAS", "AS").critical_liability / alpha, rel=1e-12
        )
        # a rescaling of the axis cannot change the multiplicative window width
        thr = attribution_thresholds(base, 0.0)
        window = (
            invasion_threshold(charged, "CAS", "AS").critical_liability
            / guard_invasion_threshold(charged)
        )
        assert window == pytest.approx(thr["window"], rel=1e-12)


def test_zero_mean_measurement_noise_averages_out(base):
    rng = np.random.default_rng(11)
    model = MeasurementModel(noise_scale=1.0)
    acc = np.zeros_like(base.unsafe_count)
    n_draws = 4000
    for _ in range(n_draws):
        acc += measured_tables(base, model, rng=rng).unsafe_count
    acc /= n_draws
    averaged = dataclasses.replace(base, unsafe_count=acc)
    # the mean channel converges to the true one at the Monte Carlo rate
    assert np.abs(acc - base.unsafe_count).max() < 6.0 / np.sqrt(n_draws)
    assert guard_invasion_threshold(averaged) == pytest.approx(
        guard_invasion_threshold(base), rel=0.05
    )


def test_misattribution_is_the_only_deforming_term(base):
    assert not measurement_is_inert(base, MeasurementModel(attribution=0.2))
    assert measurement_is_inert(base, MeasurementModel(offset=-4.0))


def test_misattribution_widens_the_window_monotonically(base):
    widths = [attribution_thresholds(base, q)["window"] for q in (0.0, 0.1, 0.3, 0.5, 0.7)]
    assert all(b > a for a, b in zip(widths, widths[1:]))
    assert widths[0] == pytest.approx(10.007, rel=1e-3)


def test_misattribution_upper_edge_has_the_closed_form(base):
    """``L*(q) = L*(0) / (1 - q)``, because ``AS`` has a spotless record."""
    zero = invasion_threshold(base, "CAS", "AS").critical_liability
    for q in (0.1, 0.25, 0.5, 0.9):
        got = attribution_thresholds(base, q)["CAS_into_AS"]
        assert got == pytest.approx(zero / (1.0 - q), rel=1e-12)


def test_misattribution_barely_moves_the_guard_threshold(base):
    base_guard = guard_invasion_threshold(base)
    worst = max(
        abs(attribution_thresholds(base, q)["guard"] - base_guard) / base_guard
        for q in (0.1, 0.25, 0.5, 0.75, 1.0)
    )
    assert worst < 0.13


def test_safe_face_stays_neutral_under_any_measurement(base):
    for model in (
        MeasurementModel(attribution=0.5),
        MeasurementModel(gain=0.3, attribution=0.9),
    ):
        assert safe_face_is_neutral(measured_tables(base, model))


# --------------------------------------------------------------------------
# lagged enforcement moves no rest point
# --------------------------------------------------------------------------


def test_delay_preserves_the_attractors(base):
    idx = [base.strategies.index(s) for s in ("AS", "CS", "CAS")]
    sel = np.ix_(idx, idx)
    a, m = base.payoff[sel], base.unsafe_count[sel]
    liability = 20.0
    scale = float(np.ptp(a - liability * m))
    x0 = np.array([0.2, 0.5, 0.3])
    undelayed = replicator_attractor(a - liability * m, x0)
    delayed = delayed_replicator(
        a / scale, m / scale, liability, x0, tau=5.0, t_end=400.0, dt=0.02
    )
    # both land on the neutral AS-CS face, which is a continuum of rest points:
    # the delay chooses a different point of it, not a different attractor
    assert undelayed[2] < 1e-6 and delayed[2] < 1e-6
    for end in (undelayed, delayed):
        assert np.abs(replicator_field(end, a - liability * m)).max() < 1e-8


# --------------------------------------------------------------------------
# assortative matching
# --------------------------------------------------------------------------


def test_assortment_is_the_identity_at_zero(base):
    tr = assorted_tables(base, 0.0)
    assert np.allclose(tr.payoff, base.payoff)
    assert np.allclose(tr.unsafe_count, base.unsafe_count)


def test_assortment_transform_matches_the_definition(base):
    r = 0.3
    got = assort_matrix(base.payoff, r)
    for i in range(base.payoff.shape[0]):
        for j in range(base.payoff.shape[1]):
            want = r * base.payoff[i, i] + (1 - r) * base.payoff[i, j]
            assert got[i, j] == pytest.approx(want, rel=1e-12)


def test_assorted_fitness_equals_the_assorted_matrix_game(base):
    r, liability = 0.25, 10.0
    tr = assorted_tables(base, r)
    x = np.array([0.4, 0.1, 0.2, 0.3])
    pi = build_selection_matrix(base, liability)
    direct = r * np.diag(pi) + (1 - r) * (pi @ x)
    viamatrix = build_selection_matrix(tr, liability) @ x
    assert np.allclose(direct, viamatrix, atol=1e-12)


def test_safe_face_stays_an_exact_twin_face_under_assortment(base):
    for r in (0.0, 0.1, 0.5, 0.9, 1.0):
        assert safe_face_is_neutral(assorted_tables(base, r))


def test_guard_threshold_is_independent_of_assortment(base):
    reference = guard_invasion_threshold(base)
    for r in np.linspace(0.0, 0.95, 20):
        assert guard_invasion_threshold(assorted_tables(base, r)) == pytest.approx(
            reference, rel=1e-12
        )


def test_assortment_shrinks_the_window_and_closes_it(base):
    widths = [assortment_thresholds(base, r)["window"] for r in (0.0, 0.1, 0.2, 0.3)]
    assert all(b < a for a, b in zip(widths, widths[1:]))
    r_close = closing_assortment(base)
    assert 0.2 < r_close < 0.5
    assert assortment_thresholds(base, r_close - 0.01)["window"] > 1.0
    assert assortment_thresholds(base, r_close + 0.01)["window"] == 0.0


def test_conditional_safety_becomes_free_before_the_window_closes(base):
    r_free = next(
        r for r in np.linspace(0.0, 0.3, 3001)
        if assortment_thresholds(base, float(r))["barrier_CS"] <= 0.0
    )
    assert r_free < closing_assortment(base)
    assert r_free == pytest.approx(0.0764, abs=2e-3)


# --------------------------------------------------------------------------
# a never-forgiving conditional design
# --------------------------------------------------------------------------


def test_grim_is_a_copier_against_deterministic_opponents():
    """With no execution noise a grim trigger and a copier are twins on the
    safe face, because neither is ever triggered by a safe opponent."""
    designs = {"AS": REDUCED_DESIGNS["AS"], "CS": REDUCED_DESIGNS["CS"], "GRIM": grim(0.0)}
    tab = build_noisy_tables(designs=designs, eta=0.0)
    assert np.abs(tab.payoff - tab.payoff[0, 0]).max() < 1e-6
    assert np.abs(tab.unsafe_count).max() < 1e-9


def test_grim_locks_in_under_execution_noise():
    """A single tremble is permanent, so self-harm rises steeply with eta."""
    designs = {"GRIM": grim(0.0), "CS": REDUCED_DESIGNS["CS"]}
    self_harm = []
    for eta in (0.0, 0.01, 0.05):
        tab = build_noisy_tables(designs=designs, eta=eta)
        self_harm.append(float(tab.unsafe_frequency[0, 0]))
    assert self_harm[0] < 1e-9
    assert self_harm[1] > 3.0 * 0.01          # far above the tremble rate itself
    assert self_harm[2] > self_harm[1]


def test_grim_pool_keeps_the_safe_face_neutral():
    designs = {
        "AS": REDUCED_DESIGNS["AS"],
        "CS": REDUCED_DESIGNS["CS"],
        "CAS": REDUCED_DESIGNS["CAS"],
        "GRIM": grim(0.0),
    }
    tab = build_noisy_tables(designs=designs, eta=0.0)
    idx = [tab.strategies.index(s) for s in ("AS", "CS", "GRIM")]
    sub = tab.payoff[np.ix_(idx, idx)]
    assert np.abs(sub - sub[0, 0]).max() < 1e-6


# --------------------------------------------------------------------------
# the rate at which twinning breaks
# --------------------------------------------------------------------------


def test_face_gradient_is_first_order_in_the_tremble_rate():
    """``delta m`` on the face is ``(E[T] - 1) * eta`` to leading order."""
    horizon = RaceParams().expected_horizon
    for eta in (1e-4, 5e-4, 1e-3):
        tab = build_noisy_tables(eta=eta)
        i_as, i_cs = tab.strategies.index("AS"), tab.strategies.index("CS")
        dm = float(tab.unsafe_count[i_cs, i_as] - tab.unsafe_count[i_as, i_as])
        assert dm / eta == pytest.approx(horizon - 1.0, rel=5e-3)


def test_the_face_gradient_points_at_conditional_safety(base):
    """The perturbation favours the design that keeps the barrier high."""
    tab = build_noisy_tables(eta=1e-3)
    i_as, i_cs = tab.strategies.index("AS"), tab.strategies.index("CS")
    da = float(tab.payoff[i_cs, i_as] - tab.payoff[i_as, i_as])
    dm = float(tab.unsafe_count[i_cs, i_as] - tab.unsafe_count[i_as, i_as])
    for liability in (0.0, 4.27, 20.0, 40.0):
        assert da - liability * dm > 0.0
    assert safe_face_barrier(base, 1.0) < safe_face_barrier(base, 0.0)
