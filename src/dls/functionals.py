"""The three payoff functionals of the deployment-layer selection framework.

The interaction layer produces a *task payoff* ``pi_A`` and an externality
intensity (expected number of Unsafe actions).  Two further functionals are
derived from these primitives:

``pi_P`` (principal / selection functional)
    what the deploying principal receives, internalising a fraction
    ``lam`` of the external harm caused by its own agent.  This functional
    drives the deployment dynamics.

``pi_S`` (social functional)
    the same accounting with the external harm fully internalised.  This
    functional is *not* part of the dynamics; it is the yardstick against
    which outcomes are evaluated, and it coincides with ``pi_P`` at
    ``lam = 1``.

Their difference is the *selection wedge*

.. math:: \\Delta(i, j) = \\pi_P(i, j) - \\pi_S(i, j) = (1 - \\lambda)\\, h\\, m(i, j),

where ``m(i, j)`` is the expected number of Unsafe actions of the focal
player.  The wedge is the entire mathematical content of the separation
between the layer at which safety is engineered and the layer at which
designs are selected.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .race import RaceTables


@dataclass(frozen=True)
class Functionals:
    """Payoff matrices of the interaction, deployment and social layers."""

    strategies: tuple[str, ...]
    pi_A: np.ndarray
    """Task payoff of the focal design."""

    pi_P: np.ndarray
    """Selection functional: what the principal receives."""

    pi_S: np.ndarray
    """Social functional: task payoff net of the full external harm."""

    wedge: np.ndarray
    """``pi_P - pi_S``."""

    unsafe_frequency: np.ndarray
    """Expected fraction of Unsafe rounds, the weight-free harm observable."""

    lam: float
    harm: float

    @property
    def effective_liability(self) -> float:
        """``L = lambda * h``, the only combination entering the dynamics."""
        return self.lam * self.harm


def build_functionals(tables: RaceTables, lam: float, harm: float) -> Functionals:
    """Assemble the three payoff functionals for a liability level ``lam``.

    Parameters
    ----------
    tables:
        Output of :func:`dls.race.build_race_tables`.
    lam:
        Liability pass-through ``lambda in [0, 1]``: the fraction of the
        external harm caused by an agent that is borne by its principal.
    harm:
        External harm ``h >= 0`` imposed on third parties by one Unsafe
        action.  Expressed in the same currency as the task payoff.
    """
    if not 0.0 <= lam <= 1.0:
        raise ValueError(f"lam must lie in [0, 1], got {lam}")
    if harm < 0.0:
        raise ValueError(f"harm must be non-negative, got {harm}")

    externality = harm * tables.unsafe_count
    pi_P = tables.payoff - lam * externality
    pi_S = tables.payoff - externality
    return Functionals(
        strategies=tables.strategies,
        pi_A=tables.payoff.copy(),
        pi_P=pi_P,
        pi_S=pi_S,
        wedge=pi_P - pi_S,
        unsafe_frequency=tables.unsafe_frequency.copy(),
        lam=float(lam),
        harm=float(harm),
    )


def build_selection_matrix(tables: RaceTables, effective_liability: float) -> np.ndarray:
    """Selection functional ``pi_P`` as a function of ``L = lambda * h`` alone.

    Only the product of the liability pass-through and the per-action harm
    enters the deployment dynamics, so the two-parameter family
    ``(lambda, h)`` collapses to the single control parameter ``L``.
    """
    return tables.payoff - float(effective_liability) * tables.unsafe_count


def is_column_constant(matrix: np.ndarray, tol: float = 1e-12) -> bool:
    """Test whether ``matrix[i, j]`` is independent of the row index ``i``.

    Adding a column-constant matrix to a payoff matrix leaves the replicator
    field, the best-response correspondence and the Nash set unchanged.  A
    wedge is *strategically inert* exactly when this predicate holds.
    """
    return bool(np.all(np.abs(matrix - matrix[0, :][None, :]) <= tol))


def strategic_distortion(matrix: np.ndarray) -> float:
    """Norm of the strategically active part of ``matrix``.

    The column-constant component is the strategically inert part of a payoff
    perturbation.  Removing it (by centring each column) leaves the part that
    can move best responses; its Frobenius norm quantifies how far a wedge is
    from being inert, and vanishes exactly when
    :func:`is_column_constant` holds.
    """
    centred = matrix - matrix.mean(axis=0, keepdims=True)
    return float(np.linalg.norm(centred))


def aggregate_unsafe_frequency(x: np.ndarray, tables_or_freq: np.ndarray) -> float:
    """Population-level Unsafe frequency ``U(x) = sum_ij x_i x_j u(i, j)``.

    This is the primary welfare-relevant observable of the model.  It requires
    no welfare weights, which keeps the reported harm measure independent of
    the (necessarily arbitrary) choice of ``h``.
    """
    u = np.asarray(tables_or_freq, dtype=float)
    x = np.asarray(x, dtype=float)
    return float(x @ u @ x)


def mean_social_payoff(x: np.ndarray, pi_S: np.ndarray) -> float:
    """Population-average social payoff ``sum_ij x_i x_j pi_S(i, j)``."""
    x = np.asarray(x, dtype=float)
    return float(x @ pi_S @ x)
