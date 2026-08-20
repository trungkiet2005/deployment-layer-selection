"""Evolutionary dynamics of the deployment layer.

Two dynamics are used throughout, both driven by the *selection functional*
``pi_P`` rather than by the social functional:

* the deterministic replicator equation in an infinite population, used for
  the phase-portrait and bifurcation analysis;
* the finite-population pairwise-comparison (Fermi) process with mutation,
  used for the stationary-distribution analysis, following the reduced
  evolutionary model of the source study.

Both are evaluated with EGTtools (Fernandez Domingos et al., 2023).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.integrate import solve_ivp

import egttools
from egttools.analytical import PairwiseComparison, replicator_equation
from egttools.games import Matrix2PlayerGameHolder


# --------------------------------------------------------------------------
# infinite-population replicator dynamics
# --------------------------------------------------------------------------


def replicator_field(x: np.ndarray, payoff: np.ndarray) -> np.ndarray:
    """Right-hand side of the replicator equation for ``payoff``."""
    return replicator_equation(np.asarray(x, dtype=float), np.asarray(payoff, dtype=float))


def replicator_mutator_field(
    x: np.ndarray, payoff: np.ndarray, mutation: float = 0.0
) -> np.ndarray:
    """Replicator field with uniform design mutation.

    ``dx_i/dt = x_i (f_i - <f>) + q (1/n - x_i)`` keeps the state in the
    interior of the simplex, so a design that has been driven to a vanishing
    frequency can still re-enter.  This matters for continuation experiments,
    where a strategy driven to numerical extinction would otherwise be unable
    to invade again after a parameter change.
    """
    x = np.asarray(x, dtype=float)
    base = replicator_equation(x, np.asarray(payoff, dtype=float))
    if mutation <= 0.0:
        return base
    n = x.size
    return base + mutation * (1.0 / n - x)


def integrate_replicator(
    payoff: np.ndarray,
    x0: np.ndarray,
    t_end: float = 500.0,
    n_points: int = 2001,
    rtol: float = 1e-10,
    atol: float = 1e-12,
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the replicator equation from ``x0``.

    Returns ``(times, trajectory)`` with ``trajectory`` of shape
    ``(n_points, n_strategies)``.
    """
    payoff = np.asarray(payoff, dtype=float)

    def rhs(_t: float, x: np.ndarray) -> np.ndarray:
        x = np.clip(x, 0.0, None)
        total = x.sum()
        if total > 0:
            x = x / total
        return replicator_equation(x, payoff)

    t_eval = np.linspace(0.0, t_end, n_points)
    sol = solve_ivp(
        rhs,
        (0.0, t_end),
        np.asarray(x0, dtype=float),
        t_eval=t_eval,
        rtol=rtol,
        atol=atol,
        method="LSODA",
    )
    traj = sol.y.T
    traj = np.clip(traj, 0.0, None)
    traj /= traj.sum(axis=1, keepdims=True)
    return sol.t, traj


def replicator_attractor(
    payoff: np.ndarray,
    x0: np.ndarray,
    t_end: float = 2000.0,
) -> np.ndarray:
    """End state of the replicator flow started at ``x0``."""
    _, traj = integrate_replicator(payoff, x0, t_end=t_end, n_points=2)
    return traj[-1]


def average_replicator_attractor(
    payoff: np.ndarray,
    n_starts: int = 200,
    seed: int = 20260817,
    t_end: float = 2000.0,
) -> np.ndarray:
    """Mean end state of the replicator flow over uniform interior starts.

    Interior initial conditions are drawn uniformly from the simplex and the
    returned vector is the mean end state, i.e. the attractor mixture weighted
    by basin volume.

    Do **not** feed this vector to a non-linear observable.  When the flow is
    multistable the mean end state is a composition the dynamics never visits,
    so ``U`` of the mean is not the mean of ``U``; the difference is largest
    exactly inside the bistability window, where the answer matters.  For a
    basin-averaged observable use :func:`dls.theory.longrun_unsafe_replicator`,
    which scores each attractor before averaging.
    """
    rng = np.random.default_rng(seed)
    n = payoff.shape[0]
    ends = np.empty((n_starts, n))
    for k in range(n_starts):
        x0 = rng.dirichlet(np.ones(n))
        ends[k] = replicator_attractor(payoff, x0, t_end=t_end)
    return ends.mean(axis=0)


# --------------------------------------------------------------------------
# equilibrium notions in the symmetric two-player game
# --------------------------------------------------------------------------


def strict_nash_strategies(payoff: np.ndarray, tol: float = 1e-9) -> list[int]:
    """Indices of pure strategies that are strict symmetric Nash equilibria."""
    n = payoff.shape[0]
    out = []
    for i in range(n):
        if all(payoff[i, i] > payoff[j, i] + tol for j in range(n) if j != i):
            out.append(i)
    return out


def neutrally_stable_strategies(payoff: np.ndarray, tol: float = 1e-9) -> list[int]:
    """Indices of pure strategies that are neutrally stable (NSS).

    ``i`` is neutrally stable if it is a symmetric Nash equilibrium and, for
    every alternative best reply ``j``, it does at least as well against ``j``
    as ``j`` does against itself.
    """
    n = payoff.shape[0]
    out = []
    for i in range(n):
        if any(payoff[j, i] > payoff[i, i] + tol for j in range(n) if j != i):
            continue
        ok = True
        for j in range(n):
            if j == i or payoff[j, i] < payoff[i, i] - tol:
                continue
            if payoff[i, j] < payoff[j, j] - tol:
                ok = False
                break
        if ok:
            out.append(i)
    return out


def invades(payoff: np.ndarray, invader: int, resident: int, tol: float = 1e-9) -> bool:
    """Whether a rare ``invader`` has a selective advantage against ``resident``."""
    return bool(payoff[invader, resident] > payoff[resident, resident] + tol)


# --------------------------------------------------------------------------
# finite-population pairwise-comparison process
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class StationaryResult:
    """Stationary distribution of the finite-population process."""

    state_distribution: np.ndarray
    """Probability of each population state, indexed as in EGTtools."""

    strategy_frequencies: np.ndarray
    """Average frequency of each design in the stationary regime."""

    unsafe_frequency: float
    """Stationary population-level Unsafe frequency."""

    population_size: int
    beta: float
    mu: float


def sparse_stationary_distribution(
    transitions: sp.spmatrix, tol: float = 1e-12, max_power_iter: int = 200_000
) -> np.ndarray:
    """Stationary distribution of a row-stochastic sparse transition matrix.

    EGTtools densifies the transition matrix, which is infeasible for the
    state spaces used here (``Z = 100`` with four designs already has 176 851
    states).  We solve the singular system ``(P^T - I) pi = 0`` with the last
    equation replaced by the normalisation ``sum(pi) = 1``, and fall back on
    power iteration if the direct solve is ill-conditioned.
    """
    p = sp.csr_matrix(transitions, dtype=float)
    n = p.shape[0]
    a = (p.transpose() - sp.identity(n, format="csr")).tolil()
    a[n - 1, :] = 1.0
    b = np.zeros(n)
    b[n - 1] = 1.0

    try:
        pi = spla.spsolve(a.tocsc(), b)
        if np.all(np.isfinite(pi)) and pi.sum() > 0:
            pi = np.clip(pi, 0.0, None)
            pi /= pi.sum()
            residual = np.abs(pi @ p - pi).max()
            if residual < 1e-8:
                return pi
    except Exception:  # pragma: no cover - direct solve is the fast path
        pass

    pi = np.full(n, 1.0 / n)
    for _ in range(max_power_iter):
        nxt = pi @ p
        nxt /= nxt.sum()
        if np.abs(nxt - pi).max() < tol:
            pi = nxt
            break
        pi = nxt
    return pi


def _state_matrix(population_size: int, nb_strategies: int) -> np.ndarray:
    """Counts of every population state, shape ``(nb_states, nb_strategies)``."""
    nb_states = egttools.calculate_nb_states(population_size, nb_strategies)
    states = np.empty((nb_states, nb_strategies), dtype=float)
    for s in range(nb_states):
        states[s] = egttools.sample_simplex(s, population_size, nb_strategies)
    return states


def _finite_population_unsafe(states: np.ndarray, u: np.ndarray, Z: int) -> np.ndarray:
    """Unsafe frequency of every population state, sampling pairs without replacement.

    For a state with counts ``k``, the probability that a random ordered pair of
    distinct individuals uses designs ``(i, j)`` is
    ``k_i (k_j - delta_ij) / (Z (Z - 1))``.
    """
    k = states
    outer = k[:, :, None] * k[:, None, :]
    diag_correction = np.zeros_like(outer)
    idx = np.arange(k.shape[1])
    diag_correction[:, idx, idx] = k
    pair_counts = outer - diag_correction
    return (pair_counts * u[None, :, :]).sum(axis=(1, 2)) / (Z * (Z - 1))


def stationary_analysis(
    payoff: np.ndarray,
    unsafe_frequency: np.ndarray,
    population_size: int = 100,
    beta: float = 1.0,
    mu: float | None = None,
) -> StationaryResult:
    """Stationary distribution of the Fermi process driven by ``payoff``.

    Parameters
    ----------
    payoff:
        The *selection* functional ``pi_P``.
    unsafe_frequency:
        Matrix ``u(i, j)`` used to score states; it never enters the dynamics.
    population_size:
        Finite population size ``Z``.
    beta:
        Intensity of selection.
    mu:
        Mutation probability.  Defaults to ``1 / population_size``.
    """
    payoff = np.ascontiguousarray(np.asarray(payoff, dtype=float))
    nb_strategies = payoff.shape[0]
    if mu is None:
        mu = 1.0 / population_size

    game = Matrix2PlayerGameHolder(nb_strategies, payoff)
    evolver = PairwiseComparison(population_size, game)
    transitions = evolver.calculate_transition_matrix(beta=beta, mu=mu)
    sd = sparse_stationary_distribution(transitions)

    states = _state_matrix(population_size, nb_strategies)
    freqs = (sd[:, None] * states).sum(axis=0) / population_size
    unsafe_by_state = _finite_population_unsafe(
        states, np.asarray(unsafe_frequency, dtype=float), population_size
    )
    return StationaryResult(
        state_distribution=sd,
        strategy_frequencies=freqs,
        unsafe_frequency=float(sd @ unsafe_by_state),
        population_size=population_size,
        beta=beta,
        mu=float(mu),
    )


def stationary_analysis_sml(
    payoff: np.ndarray,
    unsafe_frequency: np.ndarray,
    population_size: int = 100,
    beta: float = 0.05,
) -> StationaryResult:
    """Stationary distribution in the small-mutation limit.

    In the limit of rare mutation the population is monomorphic almost always,
    so the process reduces to an ``n``-state embedded chain over the pure
    designs whose transition rates are fixation probabilities.  This is the
    computationally cheap route used for parameter sweeps; it agrees with the
    full chain whenever ``mu`` is small.
    """
    payoff = np.ascontiguousarray(np.asarray(payoff, dtype=float))
    nb_strategies = payoff.shape[0]
    game = Matrix2PlayerGameHolder(nb_strategies, payoff)
    evolver = PairwiseComparison(population_size, game)
    transitions, _fixations = evolver.calculate_transition_and_fixation_matrix_sml(beta=beta)
    sd = sparse_stationary_distribution(sp.csr_matrix(np.asarray(transitions, dtype=float)))

    u = np.asarray(unsafe_frequency, dtype=float)
    return StationaryResult(
        state_distribution=sd,
        strategy_frequencies=sd,
        unsafe_frequency=float(sd @ np.diag(u)),
        population_size=population_size,
        beta=beta,
        mu=0.0,
    )
