"""Robustness of the thresholds to the constants of the interaction layer."""

from __future__ import annotations

import numpy as np
import pytest

from dls.functionals import build_selection_matrix
from dls.race import RaceParams, build_race_tables
from dls.robustness import (
    effective_liability_channel,
    hysteresis_width,
    mean_exit_time,
    threshold_grid,
    thresholds_for,
    unsafe_mass,
)
from dls.theory import face_equilibrium, invasion_threshold

POOL3 = ("AS", "CS", "CAS")


def test_thresholds_reproduce_the_baseline():
    t = thresholds_for(prize=100.0, p_max=0.6)
    base = build_race_tables(RaceParams(prize=100.0, p_max=0.6))
    assert t.l_cas_invades_as == pytest.approx(
        invasion_threshold(base, "CAS", "AS").critical_liability
    )
    assert t.l_cas_invades_cs == pytest.approx(
        invasion_threshold(base, "CAS", "CS").critical_liability
    )
    assert t.barrier_ratio == pytest.approx(77.67, rel=1e-3)
    assert t.window_width == pytest.approx(10.0, rel=1e-2)


def test_the_protecting_liability_scales_with_the_prize():
    """L*/B stays in a narrow band, so the requirement is not an artefact of B."""
    grid = threshold_grid(np.array([10.0, 50.0, 100.0, 400.0]), np.array([0.1, 0.6]))
    ratios = [t.normalised()["L_CAS_to_AS_over_B"] for t in grid]
    assert min(ratios) > 0.35 and max(ratios) < 0.65


def test_the_bistability_window_exists_across_the_whole_grid():
    grid = threshold_grid(
        np.array([10.0, 20.0, 50.0, 100.0, 200.0, 400.0]),
        np.array([0.1, 0.3, 0.6, 0.9]),
    )
    widths = np.array([t.window_width for t in grid])
    assert np.all(widths > 1.0)
    assert widths.min() > 4.0 and widths.max() < 13.0


def test_high_private_risk_protects_conditional_safety_for_free():
    t = thresholds_for(prize=100.0, p_max=0.9)
    assert t.l_cas_invades_cs < 0.0     # CAS cannot invade CS at any L >= 0
    assert t.l_cas_invades_as > 30.0    # unconditional safety still needs liability


def test_hysteresis_width_matches_across_erosion_channels():
    assert hysteresis_width(0.9, "linear") == pytest.approx(10.0)
    assert hysteresis_width(0.0, "saturating", kappa=9.0) == pytest.approx(10.0)
    assert effective_liability_channel(1.0, 1.0, channel="linear", theta=0.9) == \
        pytest.approx(effective_liability_channel(1.0, 1.0, channel="saturating", kappa=9.0))
    with pytest.raises(ValueError):
        hysteresis_width(1.0, "linear")
    with pytest.raises(ValueError):
        hysteresis_width(0.5, "nonsense")


def test_exit_time_from_the_unsafe_attractor_grows_with_selection_intensity():
    base = build_race_tables(RaceParams(p_max=0.6))
    sub = base.subset(POOL3)
    pi_p = build_selection_matrix(sub, 10.0)
    eq = face_equilibrium(sub, "AS", "CAS", 10.0)
    assert eq.fraction_second is not None

    Z = 30
    counts = np.zeros(3)
    counts[POOL3.index("CAS")] = round(eq.fraction_second * Z)
    counts[POOL3.index("AS")] = Z - counts[POOL3.index("CAS")]

    times = [
        mean_exit_time(pi_p, Z, beta, 1.0 / Z, POOL3.index("CAS"), counts)
        for beta in (0.02, 0.05, 0.2)
    ]
    assert all(b > a for a, b in zip(times, times[1:]))
    assert times[0] > Z  # more than one generation, i.e. not an immediate escape


def test_unsafe_mass_is_a_probability():
    base = build_race_tables(RaceParams(p_max=0.6))
    sub = base.subset(POOL3)
    from dls.dynamics import stationary_analysis

    res = stationary_analysis(build_selection_matrix(sub, 10.0), sub.unsafe_frequency,
                              population_size=30, beta=0.05, mu=1 / 30)
    m = unsafe_mass(res.state_distribution, 30, 3, POOL3.index("CAS"))
    assert 0.0 <= m <= 1.0
