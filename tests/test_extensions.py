"""Tests for the round-3 extensions: noise, charges, probes, alt dynamics."""

from __future__ import annotations

import numpy as np
import pytest

from dls import RaceParams, build_race_tables
from dls.altdynamics import (
    aspiration_field,
    attractor,
    best_response_field,
    logit_field,
)
from dls.charges import CHANNELS, charge_thresholds, charged_matrices
from dls.dynamics import replicator_field
from dls.noisy import REDUCED_DESIGNS, build_noisy_tables, generous, punisher
from dls.probes import probe_scores, separating_probe_sets
from dls.ratchet import RatchetParams
from dls.theory import guard_invasion_threshold, invasion_threshold


@pytest.fixture(scope="module")
def base():
    return build_race_tables(RaceParams())


# --------------------------------------------------------------------------
# the noisy evaluator must reduce to the deterministic one
# --------------------------------------------------------------------------


def test_noisy_tables_reproduce_deterministic_at_zero_noise(base):
    noisy = build_noisy_tables(eta=0.0)
    assert noisy.strategies == base.strategies
    # the only discrepancy is the shorter horizon truncation
    assert np.abs(noisy.payoff - base.payoff).max() < 1e-4
    assert np.abs(noisy.unsafe_count - base.unsafe_count).max() < 1e-4
    assert np.abs(noisy.unsafe_frequency - base.unsafe_frequency).max() < 1e-6


def test_safe_face_neutrality_is_exact_only_without_noise():
    exact = build_noisy_tables(("AS", "CS"), eta=0.0)
    assert np.abs(exact.payoff - exact.payoff[0, 0]).max() < 1e-4
    noisy = build_noisy_tables(("AS", "CS"), eta=0.02)
    # CS is strictly favoured on the face once trembles are retaliated
    assert noisy.payoff[1, 0] > noisy.payoff[0, 0] + 1.0
    assert noisy.unsafe_frequency[1, 1] > noisy.unsafe_frequency[0, 0]


def test_punisher_and_generous_are_well_formed():
    pun = punisher(2)
    assert pun.n_states == 4
    # plays Unsafe exactly while the counter is positive
    assert pun.unsafe_prob[0] == 0.0 and pun.unsafe_prob[1] == 1.0
    gen = generous("CS", 0.25)
    assert gen.unsafe_prob[1] == pytest.approx(0.75)
    with pytest.raises(ValueError):
        punisher(0)
    with pytest.raises(ValueError):
        generous("AS", 0.5)


def test_noise_narrows_but_does_not_close_the_bistability_window():
    widths = []
    for eta in (0.0, 0.05, 0.10):
        tab = build_noisy_tables(eta=eta)
        lower = guard_invasion_threshold(tab)
        upper = invasion_threshold(tab, "CAS", "AS").critical_liability
        assert upper > lower > 0.0
        widths.append(upper / lower)
    assert widths[0] > widths[1] > widths[2] > 1.0


def test_weak_dominance_fails_against_a_harsher_punisher():
    designs = dict(REDUCED_DESIGNS)
    designs["PUN2"] = punisher(2)
    tab = build_noisy_tables(designs, eta=0.0)
    i_cas = tab.strategies.index("CAS")
    i_au = tab.strategies.index("AU")
    j = tab.strategies.index("PUN2")
    assert tab.payoff[i_cas, j] < tab.payoff[i_au, j]
    # but the charge on the extra unsafe action restores it at high liability
    gap = lambda L: (  # noqa: E731
        (tab.payoff[i_cas, j] - tab.payoff[i_au, j])
        - L * (tab.unsafe_count[i_cas, j] - tab.unsafe_count[i_au, j])
    )
    assert gap(0.0) < 0.0 < gap(20.0)


# --------------------------------------------------------------------------
# non-linear charges
# --------------------------------------------------------------------------


def test_linear_channel_reproduces_the_baseline_thresholds(base):
    thr = charge_thresholds(base, "linear")
    assert thr["guard"] == pytest.approx(guard_invasion_threshold(base))
    assert thr["CAS_into_AS"] == pytest.approx(
        invasion_threshold(base, "CAS", "AS").critical_liability
    )
    assert np.allclose(charged_matrices(base, "linear", 3.0), base.payoff - 3.0 * base.unsafe_count)


def test_every_charge_shape_is_normalised_and_increasing(base):
    m_max = float(base.unsafe_count.max())
    grid = np.linspace(0.0, m_max, 25)
    for name, channel in CHANNELS.items():
        phi = channel.apply(grid, m_max)
        assert phi[0] == pytest.approx(0.0, abs=1e-9), name
        assert phi[-1] == pytest.approx(m_max, rel=1e-9), name
        assert np.all(np.diff(phi) >= -1e-12), name


def test_de_minimis_charge_never_protects_unconditional_safety(base):
    thr = charge_thresholds(base, "threshold")
    # CAS exploits AS with a single unsafe action, which the rule does not charge
    assert not np.isfinite(thr["CAS_into_AS"])
    # the window is therefore unbounded while the guard threshold stays finite
    assert np.isfinite(thr["guard"])


def test_saturating_charges_narrow_the_window(base):
    linear = charge_thresholds(base, "linear")
    for name in ("concave", "capped"):
        thr = charge_thresholds(base, name)
        assert thr["CAS_into_AS"] / thr["guard"] < linear["CAS_into_AS"] / linear["guard"]


# --------------------------------------------------------------------------
# probes
# --------------------------------------------------------------------------


def _margin(tables, probes):
    """Width of the band of strictnesses that admits exactly {AS, CS}."""
    s = probe_scores(tables, probes)
    return min(s["AU"], s["CAS"]) - max(s["AS"], s["CS"])


def test_a_reciprocating_probe_widens_the_separating_band(base):
    assert _margin(base, ("AS",)) == pytest.approx(0.132, abs=5e-4)
    assert _margin(base, ("CS",)) == pytest.approx(0.539, abs=5e-4)
    assert _margin(base, ("CAS",)) == pytest.approx(0.539, abs=5e-4)


def test_the_margin_takes_exactly_two_values(base):
    """0.539 with a conditional probe and no AU probe, 0.132 otherwise."""
    from itertools import combinations

    for size in range(1, 5):
        for probes in combinations(base.strategies, size):
            wide = ("AU" not in probes) and bool({"CS", "CAS"} & set(probes))
            expected = 0.539 if wide else 0.132
            assert _margin(base, probes) == pytest.approx(expected, abs=5e-4), probes


def test_a_hostile_probe_destroys_the_margin(base):
    """AU makes conditional safety look unsafe, because it retaliates throughout."""
    scores = probe_scores(base, ("CS", "AU"))
    assert scores["CS"] == pytest.approx(0.868, abs=5e-4)
    assert _margin(base, ("CS", "AU")) < _margin(base, ("CS",))


def test_separating_sets_include_the_adversarial_pair(base):
    sets = {tuple(p) for p, _, _ in separating_probe_sets(base, ("AS", "CS"), max_size=2)}
    assert ("AS", "CAS") in sets


# --------------------------------------------------------------------------
# alternative dynamics
# --------------------------------------------------------------------------


def test_alternative_fields_are_tangent_to_the_simplex(base):
    payoff = base.payoff - 5.0 * base.unsafe_count
    x = np.array([0.4, 0.1, 0.3, 0.2])
    for field in (
        logit_field(x, payoff, 2.0),
        best_response_field(x, payoff),
        aspiration_field(x, payoff, 40.0, 0.5),
    ):
        assert field.sum() == pytest.approx(0.0, abs=1e-12)


def test_non_imitative_dynamics_do_not_preserve_the_neutral_face(base):
    """The face is a rest set only for imitative dynamics, not for logit or BR.

    This is claim (i) versus the caveat after Proposition "The thresholds are
    properties of pi_P": logit and best response replenish a vanishing design
    at a rate that does not vanish with its frequency, so they contract the
    neutral face to its barycentre instead of leaving it fixed.
    """
    sub = base.subset(("AS", "CS"))
    payoff = sub.payoff - 7.0 * sub.unsafe_count
    x = np.array([0.3, 0.7])
    # the replicator field does vanish on the face
    assert np.abs(replicator_field(x, payoff)).max() < 1e-12
    # logit and best response do not
    assert np.abs(logit_field(x, payoff, 5.0)).max() == pytest.approx(0.2, abs=1e-9)
    assert np.abs(best_response_field(x, payoff)).max() == pytest.approx(0.2, abs=1e-9)
    for kind in ("logit", "best_response"):
        end = attractor(payoff, x, kind=kind, beta=5.0)
        assert end == pytest.approx(np.array([0.5, 0.5]), abs=1e-3)


def test_valley_edge_is_the_same_under_logit_and_replicator(base):
    """Both dynamics leave the safe attractor exactly at the guard threshold."""
    sub = base.subset(("AS", "CS", "CAS"))
    edge = guard_invasion_threshold(base)
    x0 = np.array([0.34, 0.33, 0.33])
    below = attractor(sub.payoff - (edge - 0.5) * sub.unsafe_count, x0, kind="logit", beta=10.0)
    above = attractor(sub.payoff - (edge + 0.5) * sub.unsafe_count, x0, kind="logit", beta=10.0)
    u = sub.unsafe_frequency
    assert float(below @ u @ below) < 0.1
    assert float(above @ u @ above) > 0.2


# --------------------------------------------------------------------------
# ratchet channels
# --------------------------------------------------------------------------


def test_erosion_channels_share_a_residual_fraction():
    linear = RatchetParams(channel="linear", theta=0.9)
    saturating = RatchetParams(channel="saturating", kappa=9.0)
    assert linear.residual_fraction == pytest.approx(saturating.residual_fraction)
    assert linear.effective_liability(5.0, 1.0) == pytest.approx(
        saturating.effective_liability(5.0, 1.0)
    )
    # and agree at the other endpoint by the normalisation
    assert linear.effective_liability(5.0, 0.0) == pytest.approx(5.0)
    assert saturating.effective_liability(5.0, 0.0) == pytest.approx(5.0)


def test_erosion_is_monotone_in_the_ratchet_variable():
    for params in (
        RatchetParams(channel="linear", theta=0.6),
        RatchetParams(channel="saturating", kappa=3.0),
    ):
        values = [params.effective_liability(4.0, z) for z in np.linspace(0.0, 1.0, 11)]
        assert np.all(np.diff(values) <= 1e-12)


def test_unknown_channel_is_rejected():
    with pytest.raises(ValueError):
        RatchetParams(channel="quadratic").residual_fraction
