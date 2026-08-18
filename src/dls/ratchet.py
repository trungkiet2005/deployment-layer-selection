"""Eco-evolutionary ratchet: irreversible diffusion of deployed capability.

Deployed capability does not disappear.  We couple the deployment dynamics to
a monotone, non-decreasing environmental state ``z in [0, 1]`` measuring the
stock of diffused unsafe capability,

.. math::

    \\dot{x} = \\mathrm{Rep}\\big(x;\\ \\pi_P(L_{\\mathrm{eff}}(z))\\big),
    \\qquad
    \\dot{z} = \\varepsilon\\, U(x)\\,(1 - z) \\ \\ge 0 ,

with an enforcement-erosion channel

.. math:: L_{\\mathrm{eff}}(z) = L\\,(1 - \\theta z).

The mechanism is that attribution of harm becomes harder as an unsafe
capability proliferates, so the *effective* liability that reaches a principal
decays with the diffused stock.  Because ``z`` cannot decrease, the coupled
system is path dependent: the ratchet turns a reversible parameter change into
an irreversible regime change.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .dynamics import replicator_mutator_field
from .functionals import build_selection_matrix
from .race import RaceTables


@dataclass(frozen=True)
class RatchetParams:
    """Parameters of the coupled eco-evolutionary system.

    ``channel`` selects the erosion law.  Both admissible laws are continuous,
    non-increasing in ``z`` and equal to ``L`` at ``z = 0``; they differ only in
    shape, and the hysteresis width depends on them through the single number
    :attr:`residual_fraction`.
    """

    theta: float = 0.9
    """Fractional erosion of the effective liability at full diffusion (linear channel)."""

    kappa: float = 9.0
    """Saturation constant of the ``L / (1 + kappa z)`` channel."""

    epsilon: float = 0.05
    """Time-scale separation between design selection and capability diffusion."""

    mutation: float = 1e-4
    """Uniform design mutation, so a rare design can always re-enter."""

    channel: str = "linear"
    """``"linear"`` for ``L (1 - theta z)``, ``"saturating"`` for ``L / (1 + kappa z)``."""

    @property
    def residual_fraction(self) -> float:
        """``rho = L_eff(1) / L``, the enforcement that survives full diffusion."""
        if self.channel == "linear":
            return float(max(1.0 - self.theta, 0.0))
        if self.channel == "saturating":
            return float(1.0 / (1.0 + self.kappa))
        raise ValueError("unknown erosion channel %r" % self.channel)

    def effective_liability(self, base_liability: float, z: float) -> float:
        z = float(np.clip(z, 0.0, 1.0))
        if self.channel == "linear":
            return float(max(base_liability * (1.0 - self.theta * z), 0.0))
        if self.channel == "saturating":
            return float(base_liability / (1.0 + self.kappa * z))
        raise ValueError("unknown erosion channel %r" % self.channel)


def coupled_field(
    state: np.ndarray,
    tables: RaceTables,
    base_liability: float,
    params: RatchetParams,
) -> np.ndarray:
    """Right-hand side of the coupled ``(x, z)`` system."""
    n = len(tables.strategies)
    x = np.clip(state[:n], 0.0, None)
    total = x.sum()
    if total > 0:
        x = x / total
    z = float(np.clip(state[n], 0.0, 1.0))

    pi_p = build_selection_matrix(tables, params.effective_liability(base_liability, z))
    dx = replicator_mutator_field(x, pi_p, mutation=params.mutation)

    unsafe = float(x @ tables.unsafe_frequency @ x)
    dz = params.epsilon * unsafe * (1.0 - z)
    return np.concatenate([dx, [dz]])


def integrate_coupled(
    tables: RaceTables,
    base_liability: float,
    params: RatchetParams,
    x0: np.ndarray,
    z0: float = 0.0,
    t_end: float = 3000.0,
    n_points: int = 2,
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the coupled system; returns ``(times, states)``."""
    state0 = np.concatenate([np.asarray(x0, dtype=float), [z0]])
    t_eval = np.linspace(0.0, t_end, n_points)
    sol = solve_ivp(
        lambda _t, s: coupled_field(s, tables, base_liability, params),
        (0.0, t_end),
        state0,
        t_eval=t_eval,
        rtol=1e-9,
        atol=1e-11,
        method="LSODA",
    )
    return sol.t, sol.y.T


@dataclass(frozen=True)
class HysteresisSweep:
    """Quasi-static continuation of the coupled system in the base liability."""

    liability_values: np.ndarray
    unsafe_forward: np.ndarray
    unsafe_backward: np.ndarray
    z_forward: np.ndarray
    z_backward: np.ndarray

    @property
    def loop_area(self) -> float:
        """Area enclosed by the descending and ascending branches."""
        gap = np.abs(self.unsafe_forward - self.unsafe_backward)
        trapezoid = getattr(np, "trapezoid", np.trapz)
        return float(trapezoid(gap, self.liability_values))


def hysteresis_sweep(
    tables: RaceTables,
    params: RatchetParams,
    liability_values: np.ndarray,
    x0: np.ndarray | None = None,
    t_end: float = 3000.0,
) -> HysteresisSweep:
    """Sweep the base liability down and then back up, carrying the state along.

    ``liability_values`` must be increasing.  The *forward* branch traverses it
    in decreasing order, starting from a protected regime with no diffused
    capability; the *backward* branch then traverses it in increasing order,
    starting from the end state of the forward branch, so the accumulated
    ``z`` is inherited.  Because ``z`` cannot decrease, the two branches need
    not coincide, and their separation measures the irreversibility introduced
    by capability diffusion.
    """
    n = len(tables.strategies)
    if x0 is None:
        x0 = np.full(n, 1.0 / n)

    liability_values = np.asarray(liability_values, dtype=float)
    unsafe_f = np.empty_like(liability_values)
    z_f = np.empty_like(liability_values)
    unsafe_b = np.empty_like(liability_values)
    z_b = np.empty_like(liability_values)

    state = np.concatenate([np.asarray(x0, dtype=float), [0.0]])

    for k, lam in reversed(list(enumerate(liability_values))):
        _, ys = integrate_coupled(
            tables, lam, params, state[:n], float(state[n]), t_end=t_end
        )
        state = ys[-1]
        x = np.clip(state[:n], 0.0, None)
        x = x / x.sum()
        unsafe_f[k] = x @ tables.unsafe_frequency @ x
        z_f[k] = state[n]

    for k, lam in enumerate(liability_values):
        _, ys = integrate_coupled(
            tables, lam, params, state[:n], float(state[n]), t_end=t_end
        )
        state = ys[-1]
        x = np.clip(state[:n], 0.0, None)
        x = x / x.sum()
        unsafe_b[k] = x @ tables.unsafe_frequency @ x
        z_b[k] = state[n]

    return HysteresisSweep(
        liability_values=liability_values,
        unsafe_forward=unsafe_f,
        unsafe_backward=unsafe_b,
        z_forward=z_f,
        z_backward=z_b,
    )
