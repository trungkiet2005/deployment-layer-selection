"""Closed-form thresholds and the structural results of the framework.

Notation follows the manuscript.  For an ordered pair of designs ``(i, j)`` we
write ``a(i, j)`` for the task payoff and ``m(i, j)`` for the expected number
of Unsafe actions of the focal design.  The selection functional is

.. math:: \\pi_P(i, j) = a(i, j) - \\lambda h\\, m(i, j) = a(i, j) - L\\, m(i, j),

so the liability pass-through ``lambda`` and the per-action external harm
``h`` enter the deployment dynamics only through the product
``L = lambda h``, the *effective liability*.  Every invasion condition is
affine in ``L``, which yields closed-form critical values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .dynamics import (
    average_replicator_attractor,
    replicator_attractor,
    stationary_analysis,
    stationary_analysis_sml,
)
from .functionals import build_selection_matrix, is_column_constant, strategic_distortion
from .race import RaceTables


# --------------------------------------------------------------------------
# pairwise invasion thresholds
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class InvasionThreshold:
    """Critical effective liability for one invasion attempt."""

    invader: str
    resident: str
    payoff_gain: float
    """``a(i, j) - a(j, j)``, the task-payoff advantage of a rare invader."""

    harm_gain: float
    """``m(i, j) - m(j, j)``, the excess Unsafe actions of a rare invader."""

    critical_liability: float | None
    """``L`` at which the invasion advantage vanishes; ``None`` if unbounded."""

    direction: str
    """``"invades_below"``, ``"invades_above"`` or ``"liability_independent"``."""

    def invades_at(self, effective_liability: float) -> bool:
        """Whether the invader has a selective advantage at ``L``."""
        if self.direction == "liability_independent":
            return self.payoff_gain > 0.0
        assert self.critical_liability is not None
        if self.direction == "invades_below":
            return effective_liability < self.critical_liability
        return effective_liability > self.critical_liability


def invasion_threshold(tables: RaceTables, invader: str, resident: str) -> InvasionThreshold:
    """Closed-form critical effective liability for ``invader`` invading ``resident``."""
    i = tables.strategies.index(invader)
    j = tables.strategies.index(resident)
    payoff_gain = float(tables.payoff[i, j] - tables.payoff[j, j])
    harm_gain = float(tables.unsafe_count[i, j] - tables.unsafe_count[j, j])

    if math.isclose(harm_gain, 0.0, abs_tol=1e-12):
        return InvasionThreshold(
            invader, resident, payoff_gain, harm_gain, None, "liability_independent"
        )
    critical = payoff_gain / harm_gain
    direction = "invades_below" if harm_gain > 0 else "invades_above"
    return InvasionThreshold(invader, resident, payoff_gain, harm_gain, critical, direction)


def invasion_threshold_table(tables: RaceTables) -> list[InvasionThreshold]:
    """All ordered invasion thresholds of the reduced game."""
    return [
        invasion_threshold(tables, inv, res)
        for inv in tables.strategies
        for res in tables.strategies
        if inv != res
    ]


# --------------------------------------------------------------------------
# the safe face: neutral drift and a composition-dependent invasion barrier
# --------------------------------------------------------------------------


def safe_face_is_neutral(tables: RaceTables, tol: float = 1e-12) -> bool:
    """Whether AS and CS are exact payoff twins on the safe face.

    Unconditional and conditional safety are behaviourally indistinguishable
    against safe opponents, so the AS-CS edge carries no selection gradient
    and evolves by neutral drift alone.
    """
    idx = [tables.strategies.index(s) for s in ("AS", "CS")]
    sub = tables.payoff[np.ix_(idx, idx)]
    return bool(np.all(np.abs(sub - sub[0, 0]) <= tol))


def safe_face_barrier(tables: RaceTables, cs_fraction: float, invader: str = "CAS") -> float:
    """Effective liability needed to repel ``invader`` from a mixed safe resident.

    The resident population is the mixture ``(1 - x) AS + x CS`` on the safe
    face, which is a rest set of the dynamics because the face is neutral.
    The invader is repelled when ``L`` exceeds the returned barrier.

    The barrier is the ratio of two affine functions of ``x``,

    .. math::

        L^*(x) = \\frac{(1-x)\\,\\delta a_{AS} + x\\,\\delta a_{CS}}
                       {(1-x)\\,\\delta m_{AS} + x\\,\\delta m_{CS}},

    with ``delta a`` and ``delta m`` the payoff and harm advantages of the
    invader against each pure safe design.
    """
    x = float(cs_fraction)
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"cs_fraction must lie in [0, 1], got {x}")

    k = tables.strategies.index(invader)
    i_as = tables.strategies.index("AS")
    i_cs = tables.strategies.index("CS")
    safe_payoff = float(tables.payoff[i_as, i_as])

    da = (1 - x) * (tables.payoff[k, i_as] - safe_payoff) + x * (
        tables.payoff[k, i_cs] - safe_payoff
    )
    dm = (1 - x) * tables.unsafe_count[k, i_as] + x * tables.unsafe_count[k, i_cs]
    if math.isclose(dm, 0.0, abs_tol=1e-12):
        return math.inf if da <= 0 else math.inf
    return float(da / dm)


def critical_cs_fraction(tables: RaceTables, effective_liability: float, invader: str = "CAS") -> float:
    """Smallest share of conditional safety that repels ``invader`` at ``L``.

    Returns ``0.0`` when the safe face is protected at any composition and
    ``1.0`` when no composition is protected.
    """
    lo, hi = 0.0, 1.0
    if safe_face_barrier(tables, 0.0, invader) <= effective_liability:
        return 0.0
    if safe_face_barrier(tables, 1.0, invader) > effective_liability:
        return 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if safe_face_barrier(tables, mid, invader) > effective_liability:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------
# interior equilibria of two-design faces and their invadability
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FaceEquilibrium:
    """Interior rest point of the two-design face ``(first, second)``."""

    first: str
    second: str
    effective_liability: float
    fraction_second: float | None
    """Frequency of ``second`` at the interior rest point, or ``None``."""

    stable: bool
    """Whether the rest point is an attractor of the face (mutual invasion)."""

    unsafe_frequency: float
    """Population Unsafe frequency at the rest point (0 if none exists)."""


def face_equilibrium(
    tables: RaceTables, first: str, second: str, effective_liability: float
) -> FaceEquilibrium:
    """Interior rest point of a two-design face, in closed form.

    For the face spanned by designs ``i`` and ``j`` with selection matrix
    ``M``, write ``alpha = M[j, i] - M[i, i]`` (advantage of a rare ``j``) and
    ``gamma = M[i, j] - M[j, j]`` (advantage of a rare ``i``).  An interior
    rest point exists whenever ``alpha`` and ``gamma`` share a sign, at
    ``p = alpha / (alpha + gamma)``, and it is an attractor of the face when
    both are positive.
    """
    i = tables.strategies.index(first)
    j = tables.strategies.index(second)
    m = build_selection_matrix(tables, effective_liability)

    alpha = float(m[j, i] - m[i, i])
    gamma = float(m[i, j] - m[j, j])
    denom = alpha + gamma
    if math.isclose(denom, 0.0, abs_tol=1e-12) or alpha * gamma <= 0.0:
        return FaceEquilibrium(first, second, effective_liability, None, False, 0.0)

    p = alpha / denom
    x = np.zeros(len(tables.strategies))
    x[i], x[j] = 1.0 - p, p
    unsafe = float(x @ tables.unsafe_frequency @ x)
    return FaceEquilibrium(
        first, second, effective_liability, float(p), alpha > 0 and gamma > 0, unsafe
    )


def invades_face_equilibrium(
    tables: RaceTables,
    invader: str,
    first: str,
    second: str,
    effective_liability: float,
    tol: float = 1e-12,
) -> bool | None:
    """Whether ``invader`` grows at the interior rest point of a two-design face.

    Returns ``None`` when the face has no interior rest point.
    """
    eq = face_equilibrium(tables, first, second, effective_liability)
    if eq.fraction_second is None:
        return None
    m = build_selection_matrix(tables, effective_liability)
    i = tables.strategies.index(first)
    j = tables.strategies.index(second)
    k = tables.strategies.index(invader)
    p = eq.fraction_second
    resident_fitness = (1.0 - p) * m[i, i] + p * m[i, j]
    invader_fitness = (1.0 - p) * m[k, i] + p * m[k, j]
    return bool(invader_fitness > resident_fitness + tol)


def guard_invasion_threshold(
    tables: RaceTables, guard: str = "CS", first: str = "AS", second: str = "CAS"
) -> float:
    """Effective liability above which ``guard`` can no longer invade a face rest point.

    At an interior rest point of the ``(first, second)`` face the residents
    have equal fitness, so the growth rate of a rare ``guard`` is proportional
    to ``p [ (a(g,s) - a(f,s)) - L (m(g,s) - m(f,s)) ]``.  The sign of this
    expression does not depend on the mixture ``p``: whether a conditional
    guard can enter the unsafe attractor is a property of the liability level
    alone.
    """
    g = tables.strategies.index(guard)
    i = tables.strategies.index(first)
    j = tables.strategies.index(second)
    da = float(tables.payoff[g, j] - tables.payoff[i, j])
    dm = float(tables.unsafe_count[g, j] - tables.unsafe_count[i, j])
    if math.isclose(dm, 0.0, abs_tol=1e-12):
        return math.inf
    return da / dm


def bistability_window_exact(
    tables: RaceTables, guard: str = "CS", first: str = "AS", second: str = "CAS"
) -> tuple[float, float] | None:
    """Closed-form window of ``L`` on which the unsafe attractor coexists with ``guard``.

    The lower edge is :func:`guard_invasion_threshold`; the upper edge is the
    liability at which the interior rest point collides with the ``first``
    vertex, i.e. the critical liability of ``second`` invading ``first``.
    """
    lower = guard_invasion_threshold(tables, guard, first, second)
    upper = invasion_threshold(tables, second, first).critical_liability
    if upper is None or not math.isfinite(lower) or lower >= upper:
        return None
    return float(lower), float(upper)


def bistability_window(
    tables: RaceTables,
    guard: str = "CS",
    first: str = "AS",
    second: str = "CAS",
    grid: np.ndarray | None = None,
) -> tuple[float, float] | None:
    """Range of ``L`` on which a protected design coexists with an unsafe face.

    Inside the returned window the monomorphic ``guard`` population is
    uninvadable *and* the interior rest point of the ``(first, second)`` face
    is an attractor that ``guard`` cannot invade, so the long-run Unsafe
    frequency depends on the initial condition.
    """
    if grid is None:
        upper = max(
            (t.critical_liability or 0.0)
            for t in invasion_threshold_table(tables)
            if t.critical_liability is not None
        )
        grid = np.linspace(0.0, upper * 1.05, 4001)

    mask = []
    for lam in grid:
        eq = face_equilibrium(tables, first, second, lam)
        if not eq.stable:
            mask.append(False)
            continue
        guard_invades = invades_face_equilibrium(tables, guard, first, second, lam)
        guard_safe = not invasion_threshold(tables, second, guard).invades_at(lam)
        mask.append((guard_invades is False) and guard_safe)

    mask = np.asarray(mask)
    if not mask.any():
        return None
    idx = np.flatnonzero(mask)
    return float(grid[idx[0]]), float(grid[idx[-1]])


# --------------------------------------------------------------------------
# solo evaluation filters
# --------------------------------------------------------------------------


def solo_evaluation_scores(tables: RaceTables, reference: str = "AS") -> dict[str, float]:
    """Unsafe frequency of each design against a fully safe reference environment."""
    ref = tables.strategies.index(reference)
    return {
        s: float(tables.unsafe_frequency[k, ref]) for k, s in enumerate(tables.strategies)
    }


def evaluation_filter(
    tables: RaceTables, epsilon: float, reference: str = "AS"
) -> tuple[str, ...]:
    """Designs admitted by a solo-evaluation filter of strictness ``epsilon``.

    The filter probes each design against a fully safe reference environment
    and admits it when its Unsafe frequency does not exceed ``epsilon``.  This
    is the formal counterpart of a pre-deployment safety evaluation carried out
    on an isolated model.
    """
    scores = solo_evaluation_scores(tables, reference)
    return tuple(s for s in tables.strategies if scores[s] <= epsilon + 1e-12)


# --------------------------------------------------------------------------
# long-run observables
# --------------------------------------------------------------------------


def longrun_unsafe_replicator(
    tables: RaceTables,
    effective_liability: float,
    pool: tuple[str, ...] | None = None,
    n_starts: int = 200,
    seed: int = 20260817,
) -> float:
    """Basin-averaged long-run Unsafe frequency under replicator dynamics."""
    sub = tables if pool is None else tables.subset(pool)
    pi_p = build_selection_matrix(sub, effective_liability)
    x = average_replicator_attractor(pi_p, n_starts=n_starts, seed=seed)
    return float(x @ sub.unsafe_frequency @ x)


def attractor_unsafe_values(
    tables: RaceTables,
    effective_liability: float,
    pool: tuple[str, ...] | None = None,
    n_starts: int = 200,
    seed: int = 20260817,
    decimals: int = 3,
) -> set[float]:
    """Distinct Unsafe frequencies of the attractors reached from random starts.

    Basin *averages* depend on the measure used to draw initial conditions,
    which changes with the dimension of the pool.  The set of attractor values
    does not, so this is the pool-comparable statistic.
    """
    sub = tables if pool is None else tables.subset(pool)
    pi_p = build_selection_matrix(sub, effective_liability)
    rng = np.random.default_rng(seed)
    values = set()
    for _ in range(n_starts):
        x0 = rng.dirichlet(np.ones(len(sub.strategies)))
        x = replicator_attractor(pi_p, x0)
        values.add(round(float(x @ sub.unsafe_frequency @ x), decimals))
    return values


def matched_longrun_unsafe(
    tables: RaceTables,
    effective_liability: float,
    pool: tuple[str, ...],
    common: tuple[str, ...] = ("AS", "CS", "CAS"),
    extra_share: float = 0.05,
    n_starts: int = 200,
    seed: int = 20260817,
) -> float:
    """Basin-averaged Unsafe frequency under a pool-independent start measure.

    Initial conditions are drawn on the simplex of ``common`` designs and any
    additional design in ``pool`` is seeded with a fixed small share, so that
    pools of different size are compared from the same ecosystem rather than
    from different sampling measures.
    """
    sub = tables.subset(pool)
    pi_p = build_selection_matrix(sub, effective_liability)
    idx_common = [pool.index(s) for s in common if s in pool]
    idx_extra = [k for k in range(len(pool)) if k not in idx_common]

    rng = np.random.default_rng(seed)
    total = np.zeros(len(pool))
    for _ in range(n_starts):
        x0 = np.zeros(len(pool))
        x0[idx_common] = rng.dirichlet(np.ones(len(idx_common)))
        if idx_extra:
            x0 *= 1.0 - extra_share
            x0[idx_extra] = extra_share / len(idx_extra)
        total += replicator_attractor(pi_p, x0)
    x = total / n_starts
    return float(x @ sub.unsafe_frequency @ x)


def longrun_unsafe_stationary(
    tables: RaceTables,
    effective_liability: float,
    pool: tuple[str, ...] | None = None,
    population_size: int = 50,
    beta: float = 0.05,
    mu: float | None = None,
) -> float:
    """Stationary Unsafe frequency of the finite-population process."""
    sub = tables if pool is None else tables.subset(pool)
    pi_p = build_selection_matrix(sub, effective_liability)
    res = stationary_analysis(
        pi_p,
        sub.unsafe_frequency,
        population_size=population_size,
        beta=beta,
        mu=mu,
    )
    return res.unsafe_frequency


def longrun_unsafe_sml(
    tables: RaceTables,
    effective_liability: float,
    pool: tuple[str, ...] | None = None,
    population_size: int = 50,
    beta: float = 0.05,
) -> float:
    """Stationary Unsafe frequency in the small-mutation limit."""
    sub = tables if pool is None else tables.subset(pool)
    pi_p = build_selection_matrix(sub, effective_liability)
    res = stationary_analysis_sml(
        pi_p, sub.unsafe_frequency, population_size=population_size, beta=beta
    )
    return res.unsafe_frequency


def wedge_report(tables: RaceTables, lam: float, harm: float) -> dict[str, float]:
    """Scalar summary of how far the deployment layer distorts the social game."""
    wedge = (1.0 - lam) * harm * tables.unsafe_count
    return {
        "lambda": float(lam),
        "harm": float(harm),
        "effective_liability": float(lam * harm),
        "wedge_norm": float(np.linalg.norm(wedge)),
        "strategic_distortion": strategic_distortion(wedge),
        "is_strategically_inert": float(is_column_constant(wedge)),
    }
