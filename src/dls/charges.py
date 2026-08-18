"""Non-linear liability charges.

The baseline selection functional charges a principal ``L`` per Unsafe action,
so the charge is linear in the externality intensity ``m``.  Real liability is
rarely linear: damages can be convex in the number of incidents (escalating
penalties, loss of licence), concave (caps, insurance deductibles, settlement
practice), or capped outright.  This module replaces the linear charge by

.. math:: \\pi_P(i, j) = a(i, j) - L\\,\\varphi\\big(m(i, j)\\big)

for a strictly increasing ``varphi`` with ``varphi(0) = 0``, normalised so that
``varphi(m_max) = m_max``; the normalisation makes ``L`` comparable across
channels because the charge on a design that is Unsafe throughout is the same.

Invasion conditions are then affine in ``L`` with ``delta varphi`` in place of
``delta m``, so every closed form of the paper survives with the substitution
``delta m -> varphi(m(i,j)) - varphi(m(j,j))``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .race import RaceTables

__all__ = ["ChargeChannel", "CHANNELS", "charged_matrices", "charge_thresholds"]


@dataclass(frozen=True)
class ChargeChannel:
    """A normalised, strictly increasing charge shape ``varphi``."""

    name: str
    phi: Callable[[np.ndarray], np.ndarray]
    description: str = ""

    def apply(self, m: np.ndarray, m_max: float) -> np.ndarray:
        """Evaluate ``varphi`` on ``m`` with the normalisation ``varphi(m_max) = m_max``."""
        m = np.asarray(m, dtype=float)
        raw = self.phi(m)
        scale = float(self.phi(np.array([m_max]))[0])
        return raw * (m_max / scale) if scale > 0 else raw


CHANNELS: dict[str, ChargeChannel] = {
    "linear": ChargeChannel("linear", lambda m: m, "baseline, charge per Unsafe action"),
    "convex": ChargeChannel(
        "convex", lambda m: m**2, "escalating damages, quadratic in incidents"
    ),
    "concave": ChargeChannel(
        "concave", lambda m: np.sqrt(m), "diminishing damages, square root"
    ),
    "capped": ChargeChannel(
        "capped", lambda m: np.minimum(m, 3.0), "charge capped at three incidents"
    ),
    "threshold": ChargeChannel(
        "threshold",
        lambda m: np.clip(m - 2.0, 0.0, None),
        "no charge below two incidents, linear above",
    ),
}


def charged_matrices(
    tables: RaceTables, channel: str | ChargeChannel, liability: float
) -> np.ndarray:
    """Selection functional under a non-linear charge at level ``liability``."""
    ch = CHANNELS[channel] if isinstance(channel, str) else channel
    m_max = float(np.max(tables.unsafe_count))
    return tables.payoff - float(liability) * ch.apply(tables.unsafe_count, m_max)


def charge_thresholds(
    tables: RaceTables, channel: str | ChargeChannel
) -> dict[str, float]:
    """The four thresholds of the paper under a non-linear charge.

    Each threshold is ``delta a / delta varphi`` with ``delta varphi`` the
    charge difference that replaces ``delta m``.  ``guard`` is the threshold of
    Theorem "Guard threshold"; note that with ``varphi`` non-linear the safe
    face is still an exact twin face, because ``m`` vanishes identically on it,
    so the mixture-free criterion continues to apply.
    """
    ch = CHANNELS[channel] if isinstance(channel, str) else channel
    m_max = float(np.max(tables.unsafe_count))
    phi = ch.apply(tables.unsafe_count, m_max)
    a = tables.payoff
    idx = {s: k for k, s in enumerate(tables.strategies)}

    def pair(invader: str, resident: str) -> float:
        i, j = idx[invader], idx[resident]
        da = a[i, j] - a[j, j]
        dphi = phi[i, j] - phi[j, j]
        return float(da / dphi) if abs(dphi) > 1e-12 else float("inf")

    i_as, i_cs, i_cas = idx["AS"], idx["CS"], idx["CAS"]
    d_guard = phi[i_cs, i_cas] - phi[i_as, i_cas]
    guard = (
        float((a[i_cs, i_cas] - a[i_as, i_cas]) / d_guard)
        if abs(d_guard) > 1e-12
        else float("inf")
    )
    return {
        "CAS_into_AS": pair("CAS", "AS"),
        "CAS_into_CS": pair("CAS", "CS"),
        "CS_into_CAS": pair("CS", "CAS"),
        "guard": guard,
    }
