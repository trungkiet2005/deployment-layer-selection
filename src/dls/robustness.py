"""Robustness of the thresholds to the constants of the interaction layer.

The thresholds of the main analysis are ratios of payoff differences, so they
inherit the scale of the race prize ``B`` and the shape of the private-risk
treatment ``p_r^max``.  This module recomputes them across those constants,
measures how long the unsafe attractor survives in a finite population, and
checks the hysteresis result against a second enforcement-erosion channel.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import egttools
from egttools.analytical import PairwiseComparison
from egttools.games import Matrix2PlayerGameHolder

from .functionals import build_selection_matrix
from .race import RaceParams, build_race_tables
from .theory import (
    bistability_window_exact,
    guard_invasion_threshold,
    invasion_threshold,
)


# --------------------------------------------------------------------------
# thresholds across the constants of the race
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ThresholdSet:
    """Critical effective liabilities for one parameterisation of the race."""

    prize: float
    p_max: float
    l_cs_invades_cas: float
    l_cas_invades_cs: float
    l_as_invades_cas: float
    l_cas_invades_as: float
    l_guard: float
    window_lo: float | None
    window_hi: float | None

    @property
    def window_width(self) -> float:
        """Multiplicative width of the bistability window, 1 if it is empty."""
        if self.window_lo is None or self.window_hi is None:
            return 1.0
        return self.window_hi / self.window_lo

    @property
    def barrier_ratio(self) -> float:
        """How much cheaper unconditional safety is to invade than conditional."""
        return self.l_cas_invades_as / self.l_cas_invades_cs

    def normalised(self) -> dict[str, float]:
        """Thresholds expressed as a fraction of the race prize."""
        return {
            "L_CAS_to_AS_over_B": self.l_cas_invades_as / self.prize,
            "L_CAS_to_CS_over_B": self.l_cas_invades_cs / self.prize,
            "L_guard_over_B": self.l_guard / self.prize,
        }


def thresholds_for(prize: float, p_max: float) -> ThresholdSet:
    """All critical liabilities for a given prize and private-risk treatment."""
    tables = build_race_tables(RaceParams(prize=prize, p_max=p_max))
    window = bistability_window_exact(tables)

    def crit(inv: str, res: str) -> float:
        value = invasion_threshold(tables, inv, res).critical_liability
        return float("nan") if value is None else float(value)

    return ThresholdSet(
        prize=float(prize),
        p_max=float(p_max),
        l_cs_invades_cas=crit("CS", "CAS"),
        l_cas_invades_cs=crit("CAS", "CS"),
        l_as_invades_cas=crit("AS", "CAS"),
        l_cas_invades_as=crit("CAS", "AS"),
        l_guard=guard_invasion_threshold(tables),
        window_lo=None if window is None else window[0],
        window_hi=None if window is None else window[1],
    )


def threshold_grid(
    prizes: np.ndarray, p_maxes: np.ndarray
) -> list[ThresholdSet]:
    """Thresholds over a grid of race prizes and private-risk treatments."""
    return [thresholds_for(float(b), float(p)) for b in prizes for p in p_maxes]


# --------------------------------------------------------------------------
# how long the unsafe attractor survives in a finite population
# --------------------------------------------------------------------------


def _state_counts(population_size: int, nb_strategies: int) -> np.ndarray:
    nb_states = egttools.calculate_nb_states(population_size, nb_strategies)
    return np.array(
        [egttools.sample_simplex(s, population_size, nb_strategies) for s in range(nb_states)],
        dtype=float,
    )


def mean_exit_time(
    payoff: np.ndarray,
    population_size: int,
    beta: float,
    mu: float,
    unsafe_index: int,
    start_counts: np.ndarray,
    absorbing_threshold: int = 0,
) -> float:
    """Expected number of update steps to reach a state free of the unsafe design.

    Solves ``(I - Q) t = 1`` on the transient states, where the target set is
    every state with at most ``absorbing_threshold`` copies of the design at
    ``unsafe_index``.  The result is the escape time from the unsafe attractor
    and therefore the time scale on which the bistability of the deterministic
    model is visible in a finite population.
    """
    payoff = np.ascontiguousarray(np.asarray(payoff, dtype=float))
    nb_strategies = payoff.shape[0]
    game = Matrix2PlayerGameHolder(nb_strategies, payoff)
    evolver = PairwiseComparison(population_size, game)
    transitions = sp.csr_matrix(evolver.calculate_transition_matrix(beta=beta, mu=mu))

    counts = _state_counts(population_size, nb_strategies)
    target = counts[:, unsafe_index] <= absorbing_threshold
    transient = np.flatnonzero(~target)
    if transient.size == 0:
        return 0.0

    q = transitions[transient][:, transient]
    a = sp.identity(transient.size, format="csr") - q
    times = spla.spsolve(a.tocsc(), np.ones(transient.size))

    start_index = int(egttools.calculate_state(population_size, np.asarray(start_counts)))
    if target[start_index]:
        return 0.0
    position = int(np.searchsorted(transient, start_index))
    return float(times[position])


def unsafe_mass(
    state_distribution: np.ndarray,
    population_size: int,
    nb_strategies: int,
    unsafe_index: int,
    threshold: float = 0.25,
) -> float:
    """Stationary probability that the unsafe design exceeds a frequency threshold."""
    counts = _state_counts(population_size, nb_strategies)
    mask = counts[:, unsafe_index] / population_size > threshold
    return float(state_distribution[mask].sum())


# --------------------------------------------------------------------------
# a second enforcement-erosion channel
# --------------------------------------------------------------------------


def hysteresis_width(theta: float, channel: str = "linear", kappa: float = 1.0) -> float:
    """Multiplicative width of the hysteresis loop for a given erosion channel.

    ``linear``:     ``L_eff = L (1 - theta z)``  gives width ``1 / (1 - theta)``.
    ``saturating``: ``L_eff = L / (1 + kappa z)`` gives width ``1 + kappa``.

    Both follow from the same argument: the protected branch has ``U = 0``
    exactly, so ``z`` is frozen there and the loss threshold is the bare
    invasion threshold, while on the unsafe branch ``z`` saturates at one and
    recovery needs ``L_eff`` to exceed that same threshold.  Only the width
    depends on the channel.
    """
    if channel == "linear":
        if not 0.0 <= theta < 1.0:
            raise ValueError("theta must lie in [0, 1) for the linear channel")
        return 1.0 / (1.0 - theta)
    if channel == "saturating":
        if kappa < 0.0:
            raise ValueError("kappa must be non-negative")
        return 1.0 + kappa
    raise ValueError(f"unknown channel {channel!r}")


def effective_liability_channel(
    base_liability: float, z: float, channel: str = "linear",
    theta: float = 0.9, kappa: float = 9.0,
) -> float:
    """Effective liability under either erosion channel."""
    z = float(np.clip(z, 0.0, 1.0))
    if channel == "linear":
        return max(base_liability * (1.0 - theta * z), 0.0)
    if channel == "saturating":
        return base_liability / (1.0 + kappa * z)
    raise ValueError(f"unknown channel {channel!r}")


def selection_matrix_at(tables, base_liability: float, z: float, **kwargs) -> np.ndarray:
    """Selection matrix under an eroded liability."""
    return build_selection_matrix(
        tables, effective_liability_channel(base_liability, z, **kwargs)
    )
