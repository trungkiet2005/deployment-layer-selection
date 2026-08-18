"""Pre-deployment evaluation against a set of probe environments.

The solo filter of the main text scores a design by its Unsafe frequency
against a fully safe probe, ``s(i) = u(i, AS)``.  This module generalises the
score to an arbitrary *probe set* ``P``,

.. math:: s_P(i) = \\max_{j \\in P} u(i, j),

which is the natural formalisation of a multi-agent adversarial evaluation:
the design is placed in several counterpart environments and scored by its
worst behaviour.  The point of interest is which pools such a filter admits,
and in particular whether any probe set separates conditional safety from
conditional aggression while admitting the former.
"""

from __future__ import annotations

import numpy as np

from .race import RaceTables

__all__ = ["probe_scores", "probe_filter", "separating_probe_sets"]


def probe_scores(
    tables: RaceTables, probes: tuple[str, ...], aggregate: str = "max"
) -> dict[str, float]:
    """Score of every design against a probe set."""
    cols = [tables.strategies.index(p) for p in probes]
    block = tables.unsafe_frequency[:, cols]
    if aggregate == "max":
        scores = block.max(axis=1)
    elif aggregate == "mean":
        scores = block.mean(axis=1)
    else:
        raise ValueError("aggregate must be 'max' or 'mean'")
    return {s: float(scores[k]) for k, s in enumerate(tables.strategies)}


def probe_filter(
    tables: RaceTables,
    probes: tuple[str, ...],
    epsilon: float,
    aggregate: str = "max",
) -> tuple[str, ...]:
    """Designs admitted by a probe-set filter of strictness ``epsilon``."""
    scores = probe_scores(tables, probes, aggregate)
    return tuple(s for s in tables.strategies if scores[s] <= epsilon + 1e-12)


def separating_probe_sets(
    tables: RaceTables,
    target_pool: tuple[str, ...] = ("AS", "CS"),
    max_size: int = 2,
    aggregate: str = "max",
) -> list[tuple[tuple[str, ...], float, float]]:
    """Probe sets admitting exactly ``target_pool``, with the admissible band.

    Returns ``(probes, epsilon_low, epsilon_high)`` for every probe set of size
    at most ``max_size`` such that some strictness admits exactly
    ``target_pool``.  ``epsilon_low`` is the worst score inside the target pool
    and ``epsilon_high`` the best score outside it, so any strictness in
    ``[epsilon_low, epsilon_high)`` realises the separation.
    """
    from itertools import combinations

    out = []
    designs = tables.strategies
    for size in range(1, max_size + 1):
        for probes in combinations(designs, size):
            scores = probe_scores(tables, probes, aggregate)
            inside = [scores[s] for s in target_pool]
            outside = [scores[s] for s in designs if s not in target_pool]
            if not outside:
                continue
            lo, hi = max(inside), min(outside)
            if lo < hi - 1e-12:
                out.append((probes, float(lo), float(hi)))
    return out
