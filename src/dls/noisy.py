"""Execution noise and richer conditional designs.

The four reduced designs of :mod:`dls.race` are deterministic, which makes the
matchup quantities exactly computable but leaves open whether the results are
an artefact of that determinism.  This module evaluates the same race for a
family of *stochastic finite-state* designs under trembling-hand execution
noise ``eta``: every intended action is inverted with probability ``eta``
before it is played and before the opponent observes it.

A design is a finite-state machine with

* ``unsafe_prob[s]``: probability of *intending* Unsafe in internal state ``s``,
* ``transition[s, o]``: next internal state after own state ``s`` and the
  opponent's realised action ``o``,
* an initial state.

This covers the reduced designs (``AS``, ``AU``, ``CS``, ``CAS``), generous
variants that forgive an observed Unsafe with probability ``g``, and
``k``-round punishers that answer one observed Unsafe with ``k`` Unsafe rounds.

Evaluation is exact, not Monte Carlo.  The joint chain over
``(own state, opponent state)`` is propagated round by round together with the
race bookkeeping that the payoff needs -- the progress difference and the own
Unsafe count -- while the accumulated stage payoff is carried as a first
moment.  Because the setback probability ``q = p_max * n_U / T`` multiplies the
kept payoff, the payoff at the horizon involves ``E[n_U * s]``; carrying the
weighted mass ``W(state) = E[s * 1{state}]`` alongside the probability mass
``P(state)`` makes that expectation exact.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .race import SAFE, UNSAFE, RaceParams, RaceTables

__all__ = [
    "NoisyDesign",
    "REDUCED_DESIGNS",
    "generous",
    "punisher",
    "evaluate_noisy_matchup",
    "build_noisy_tables",
]


@dataclass(frozen=True)
class NoisyDesign:
    """A stochastic finite-state design."""

    name: str
    unsafe_prob: np.ndarray
    """``unsafe_prob[s]``: probability of intending Unsafe in internal state ``s``."""

    transition: np.ndarray
    """``transition[s, o]``: internal state after observing opponent action ``o``."""

    initial: int = 0

    @property
    def n_states(self) -> int:
        return int(np.asarray(self.unsafe_prob).size)


def _copier(first_unsafe: float, name: str, forgive: float = 0.0) -> NoisyDesign:
    """Copy the opponent's last realised action, forgiving an Unsafe w.p. ``forgive``.

    Internal state ``0`` mimics Safe, state ``1`` mimics Unsafe, state ``2`` is
    the first round, whose Unsafe intent is ``first_unsafe``.
    """
    unsafe_prob = np.array([0.0, 1.0 - forgive, first_unsafe])
    transition = np.array([[0, 1], [0, 1], [0, 1]])
    return NoisyDesign(name, unsafe_prob, transition, initial=2)


def _constant(unsafe: float, name: str) -> NoisyDesign:
    return NoisyDesign(name, np.array([unsafe]), np.array([[0, 0]]), initial=0)


REDUCED_DESIGNS: dict[str, NoisyDesign] = {
    "AS": _constant(0.0, "AS"),
    "AU": _constant(1.0, "AU"),
    "CS": _copier(0.0, "CS"),
    "CAS": _copier(1.0, "CAS"),
}


def generous(base: str, forgive: float) -> NoisyDesign:
    """Conditional design that answers an observed Unsafe with Safe w.p. ``forgive``."""
    if base not in ("CS", "CAS"):
        raise ValueError("base must be CS or CAS")
    first = 1.0 if base == "CAS" else 0.0
    return _copier(first, "G%s%g" % (base, forgive), forgive=forgive)


def punisher(rounds: int, first_unsafe: float = 0.0, name: str | None = None) -> NoisyDesign:
    """Answer one observed Unsafe with ``rounds`` Unsafe rounds, then return to Safe.

    Internal state ``j <= rounds`` is the number of punishment rounds still
    owed; the design plays Unsafe while ``j > 0``.  Observing a further Unsafe
    resets the counter.  ``rounds = 1`` reproduces the copying rule.
    """
    if rounds < 1:
        raise ValueError("rounds must be at least 1")
    n = rounds + 2                      # counter states 0..rounds, plus first round
    unsafe_prob = np.zeros(n)
    unsafe_prob[1 : rounds + 1] = 1.0
    unsafe_prob[n - 1] = first_unsafe
    transition = np.zeros((n, 2), dtype=int)
    for s in range(n):
        counter = s if s <= rounds else 0
        transition[s, SAFE] = max(counter - 1, 0)
        transition[s, UNSAFE] = rounds
    return NoisyDesign(name or ("PUN%d" % rounds), unsafe_prob, transition, initial=n - 1)


def _realised_action_probs(design: NoisyDesign, eta: float) -> np.ndarray:
    """``p[s, a]``: probability that internal state ``s`` *realises* action ``a``."""
    intent = np.clip(np.asarray(design.unsafe_prob, dtype=float), 0.0, 1.0)
    realised = intent * (1.0 - eta) + (1.0 - intent) * eta
    return np.stack([1.0 - realised, realised], axis=1)


def evaluate_noisy_matchup(
    row: NoisyDesign,
    col: NoisyDesign,
    params: RaceParams | None = None,
    eta: float = 0.0,
    max_rounds: int = 80,
) -> tuple[float, float, float]:
    """Exact ``(task payoff, Unsafe count, Unsafe frequency)`` of ``row`` vs ``col``.

    ``max_rounds`` truncates the horizon law; the residual geometric mass is
    assigned to the last atom, exactly as in
    :meth:`dls.race.RaceParams.horizon_distribution`.
    """
    params = params or RaceParams()
    t_values = np.arange(params.min_rounds, max_rounds + 1)
    probs = params.stop_prob * (1.0 - params.stop_prob) ** (t_values - params.min_rounds)
    probs[-1] = max(0.0, 1.0 - probs[:-1].sum())
    horizon_index = {int(t): k for k, t in enumerate(t_values)}

    p_row = _realised_action_probs(row, eta)
    p_col = _realised_action_probs(col, eta)
    n_r, n_c = row.n_states, col.n_states

    step = (params.step_safe, params.step_unsafe)
    half_units = np.rint(
        np.array([[step[a] - step[b] for b in (0, 1)] for a in (0, 1)]) / 0.5
    ).astype(int)

    n_d = 2 * max_rounds + 1
    d0 = max_rounds
    shape = (n_r, n_c, n_d, max_rounds + 1)
    mass = np.zeros(shape)
    weighted = np.zeros(shape)          # E[cumulative stage payoff * 1{state}]
    mass[row.initial, col.initial, d0, 0] = 1.0

    counts = np.arange(max_rounds + 1, dtype=float)
    diff = np.arange(n_d) - d0
    at_risk = diff >= 0
    prize = np.where(diff > 0, params.prize, 0.0) + np.where(
        diff == 0, params.prize / 2.0, 0.0
    )

    payoff = 0.0
    unsafe_count = 0.0
    unsafe_freq = 0.0

    for t in range(1, max_rounds + 1):
        new_mass = np.zeros(shape)
        new_weighted = np.zeros(shape)
        for a in (SAFE, UNSAFE):
            for b in (SAFE, UNSAFE):
                w = p_row[:, a][:, None] * p_col[:, b][None, :]
                if not np.any(w > 0.0):
                    continue
                stage = float(params.stage_payoffs[a, b])
                src_m = mass * w[:, :, None, None]
                src_w = weighted * w[:, :, None, None] + src_m * stage
                shift = int(half_units[a, b])
                if shift:
                    src_m = np.roll(src_m, shift, axis=2)
                    src_w = np.roll(src_w, shift, axis=2)
                if a == UNSAFE:
                    src_m = np.roll(src_m, 1, axis=3)
                    src_w = np.roll(src_w, 1, axis=3)
                sr = row.transition[:, b]
                sc = col.transition[:, a]
                for i in range(n_r):
                    for j in range(n_c):
                        new_mass[sr[i], sc[j]] += src_m[i, j]
                        new_weighted[sr[i], sc[j]] += src_w[i, j]
        mass, weighted = new_mass, new_weighted

        k = horizon_index.get(t)
        if k is None or probs[k] <= 0.0:
            continue
        m_td = mass.sum(axis=(0, 1))
        w_td = weighted.sum(axis=(0, 1))
        q = params.p_max * counts / t
        keep = np.where(at_risk[:, None], 1.0 - q[None, :], 1.0)
        if params.setback_scope == "total":
            value = keep * (w_td + prize[:, None] * m_td)
        else:
            value = w_td + keep * prize[:, None] * m_td
        n_marginal = m_td.sum(axis=0)
        expected_n = float(n_marginal @ counts)
        payoff += probs[k] * float(value.sum())
        unsafe_count += probs[k] * expected_n
        unsafe_freq += probs[k] * expected_n / t

    return float(payoff), float(unsafe_count), float(unsafe_freq)


def build_noisy_tables(
    designs: dict[str, NoisyDesign] | tuple[str, ...] | None = None,
    params: RaceParams | None = None,
    eta: float = 0.0,
    max_rounds: int = 80,
) -> RaceTables:
    """Matchup tables for a pool of stochastic designs at execution noise ``eta``."""
    params = params or RaceParams()
    if designs is None:
        designs = REDUCED_DESIGNS
    if isinstance(designs, tuple):
        designs = {name: REDUCED_DESIGNS[name] for name in designs}

    names = tuple(designs)
    n = len(names)
    a = np.zeros((n, n))
    m = np.zeros((n, n))
    u = np.zeros((n, n))
    for i, ni in enumerate(names):
        for j, nj in enumerate(names):
            a[i, j], m[i, j], u[i, j] = evaluate_noisy_matchup(
                designs[ni], designs[nj], params, eta, max_rounds=max_rounds
            )
    zeros = np.zeros((n, n))
    return RaceTables(
        strategies=names,
        payoff=a,
        unsafe_count=m,
        unsafe_frequency=u,
        win_probability=zeros,
        tie_probability=zeros,
        setback_probability=zeros,
        params=params,
    )
