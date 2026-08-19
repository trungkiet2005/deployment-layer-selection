"""Assortative matching, and what it does to the liability valley.

The results of the main text assume random matching.  Population structure --
a network, a market with repeat business, clusters of interoperating agents --
makes an agent more likely to meet its own kind than chance dictates.  The
standard deterministic idealisation is *assortment*: with probability ``r`` a
design interacts with a copy of itself, and with probability ``1 - r`` with a
partner drawn from the population at large.  Expected fitness is then

.. math::
    f_i(x) = r\\,\\pi(i, i) + (1 - r) \\sum_j x_j\\, \\pi(i, j)
           = \\sum_j x_j\\,\\tilde\\pi(i, j),
    \\qquad \\tilde\\pi(i, j) = r\\,\\pi(i, i) + (1 - r)\\,\\pi(i, j),

so an assorted population plays an ordinary matrix game with the transformed
matrix :math:`\\tilde\\pi`.  Two consequences make the transformation useful
here rather than merely convenient.

First, ``a`` and ``m`` transform separately and the transformation is linear,
so :math:`\\tilde\\pi` is still affine in the effective liability and every
closed form of the paper survives with ``a`` and ``m`` replaced by their
assorted counterparts.

Second, the safe face is still an exact twin face at every ``r``, because the
assortment correction is a self-interaction term and the two safe designs are
self-identical: ``AS`` and ``CS`` earn the same payoff and cause the same
(zero) harm against themselves as against each other.  The same cancellation
makes the guard threshold exactly independent of ``r``, which is the reason
assortment moves only the upper edge of the bistable window.

The harm observable is assorted as well, since it counts the interactions that
actually take place.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from .race import RaceTables

__all__ = ["assort_matrix", "assorted_tables", "assortment_thresholds", "closing_assortment"]


def assort_matrix(matrix: np.ndarray, r: float) -> np.ndarray:
    """``r * diag(matrix)`` broadcast over rows, plus ``(1 - r) * matrix``."""
    x = np.asarray(matrix, dtype=float)
    return r * np.diag(x)[:, None] + (1.0 - r) * x


def assorted_tables(tables: RaceTables, r: float) -> RaceTables:
    """Race tables of an assorted population with assortment level ``r``.

    ``payoff``, ``unsafe_count`` and ``unsafe_frequency`` are all transformed:
    the first two because they enter the selection functional, the third
    because the population harm counts the interactions that occur, and under
    assortment a fraction ``r`` of those are self-interactions.
    """
    r = float(r)
    if not 0.0 <= r <= 1.0:
        raise ValueError(f"r must lie in [0, 1], got {r}")
    return dataclasses.replace(
        tables,
        payoff=assort_matrix(tables.payoff, r),
        unsafe_count=assort_matrix(tables.unsafe_count, r),
        unsafe_frequency=assort_matrix(tables.unsafe_frequency, r),
    )


def assortment_thresholds(tables: RaceTables, r: float) -> dict[str, float]:
    """The thresholds of the paper in an assorted population."""
    from .theory import guard_invasion_threshold, invasion_threshold, safe_face_barrier

    tr = assorted_tables(tables, r)
    guard = guard_invasion_threshold(tr)
    upper = invasion_threshold(tr, "CAS", "AS").critical_liability
    entry = invasion_threshold(tr, "CAS", "CS").critical_liability
    closed = upper is None or guard <= 0.0 or upper <= guard
    width = 0.0 if closed else float(upper / guard)
    return {
        "r": float(r),
        "guard": float(guard),
        "CAS_into_AS": float(upper) if upper is not None else float("inf"),
        "CAS_into_CS": float(entry) if entry is not None else float("inf"),
        "barrier_AS": float(safe_face_barrier(tr, 0.0)),
        "barrier_CS": float(safe_face_barrier(tr, 1.0)),
        "window": width,
    }


def closing_assortment(tables: RaceTables, tol: float = 1e-10) -> float:
    """Smallest assortment at which the bistable window closes.

    The lower edge of the window is the guard threshold, which does not move
    with ``r``; the upper edge is the liability at which conditional aggression
    can no longer invade unconditional safety, which falls with ``r``.  The
    window closes when the two meet.  Returns ``1.0`` if they never do.
    """
    from .theory import guard_invasion_threshold, invasion_threshold

    def gap(r: float) -> float:
        tr = assorted_tables(tables, r)
        upper = invasion_threshold(tr, "CAS", "AS").critical_liability
        upper = float(upper) if upper is not None else float("inf")
        return upper - guard_invasion_threshold(tr)

    if gap(1.0) > 0.0:
        return 1.0
    lo, hi = 0.0, 1.0
    while hi - lo > tol:
        mid = 0.5 * (lo + hi)
        if gap(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
