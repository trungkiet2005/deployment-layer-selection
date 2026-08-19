"""What the principal can see: imperfect measurement of the externality.

The selection functional of the main text charges a principal for the harm its
own agent caused,

.. math:: \\pi_P(i, j) = a(i, j) - L\\, m(i, j),

which presumes that the number of Unsafe actions is measured without error and
attributed to the right party.  Neither holds in practice: incident data are
noisy, systematically incomplete, and frequently record *that* an interaction
went wrong without recording *who moved first*.  This module replaces the true
externality intensity by a measured one and asks which of the paper's
thresholds survive.

The measurement channel is the affine family

.. math:: \\hat m(i, j) = \\alpha\\, m(i, j) + q\\, m(j, i) + c + \\varepsilon_{ij},

with

``gain`` :math:`\\alpha > 0`
    systematic under- or over-reporting of an agent's own incidents;
``attribution`` :math:`q \\ge 0`
    the weight the principal puts on the *counterparty's* incident record,
    which is what an incident report that does not identify the initiator
    effectively charges;
``offset`` :math:`c`
    a baseline charge levied on every deployment regardless of conduct;
``eps``
    zero-mean measurement noise, drawn independently of everything else.

Three of the four are harmless and one is not, and the asymmetry is the point
of the module:

* zero-mean noise is *exactly* inert, because the selection functional is
  linear in the charge base and therefore depends on the measurement only
  through its conditional expectation;
* a constant offset is exactly inert by column-constant invariance, and so is
  any error that depends only on the counterparty;
* a gain is a pure reparameterisation, mapping every threshold
  :math:`L^{*}` to :math:`L^{*}/\\alpha`, so it rescales the liability axis
  without deforming anything on it;
* misattribution is the one term that deforms the dynamics, and it deforms
  them in the dangerous direction, because the victim of a first strike is by
  construction the party with the clean record.

The lag channel is separate and is handled by :func:`delayed_replicator`: a
principal who charges on an incident window of length ``tau`` reacts to the
population composition as it was, not as it is.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

import numpy as np

from .race import RaceTables

__all__ = [
    "MeasurementModel",
    "measured_tables",
    "measurement_is_inert",
    "attribution_thresholds",
    "delayed_replicator",
]


@dataclass(frozen=True)
class MeasurementModel:
    """Affine channel between true and charged externality intensity."""

    gain: float = 1.0
    """``alpha``: fraction of an agent's own incidents that reach the record."""

    attribution: float = 0.0
    """``q``: weight placed on the counterparty's incidents."""

    offset: float = 0.0
    """``c``: charge levied on every deployment irrespective of conduct."""

    noise_scale: float = 0.0
    """Standard deviation of the zero-mean measurement error, for sampling."""

    def __post_init__(self) -> None:
        if self.gain < 0.0:
            raise ValueError(f"gain must be non-negative, got {self.gain}")
        if self.attribution < 0.0:
            raise ValueError(f"attribution must be non-negative, got {self.attribution}")
        if self.gain + self.attribution <= 0.0:
            raise ValueError("the channel must charge something: gain + attribution > 0")
        if self.noise_scale < 0.0:
            raise ValueError(f"noise_scale must be non-negative, got {self.noise_scale}")

    @property
    def is_unbiased_in_attribution(self) -> bool:
        """Whether the channel charges an agent for its own conduct only."""
        return self.attribution == 0.0

    @classmethod
    def misattribution(cls, q: float) -> "MeasurementModel":
        """The blame-splitting channel ``hat m = (1 - q) m(i,j) + q m(j,i)``.

        A fixed quantity of blame is allocated between the two parties to an
        interaction, of which a fraction ``q`` lands on the wrong one.  Holding
        the total charge fixed is what keeps ``L`` comparable across ``q``: the
        additive variant ``m + q m^T`` describes the same deformation composed
        with a gain of ``1 + q``, and therefore differs from this one only by a
        rescaling of the liability axis.
        """
        q = float(q)
        if not 0.0 <= q <= 1.0:
            raise ValueError(f"q must lie in [0, 1], got {q}")
        return cls(gain=1.0 - q, attribution=q)


def measured_tables(
    tables: RaceTables,
    model: MeasurementModel,
    rng: np.random.Generator | None = None,
) -> RaceTables:
    """Race tables whose charge base is the *measured* externality intensity.

    Only ``unsafe_count``, which is the base of the liability charge, is
    replaced.  ``unsafe_frequency`` is the harm actually inflicted on third
    parties and is left untouched: mismeasuring harm does not undo it, and the
    welfare observable of the paper must continue to count the real thing.

    Passing an ``rng`` draws one realisation of the measurement error, which is
    used only to demonstrate that the *expected* charge is what matters; the
    thresholds are computed from the noiseless mean channel.
    """
    m = np.asarray(tables.unsafe_count, dtype=float)
    charged = model.gain * m + model.attribution * m.T + model.offset
    if rng is not None and model.noise_scale > 0.0:
        charged = charged + rng.normal(0.0, model.noise_scale, size=m.shape)
    return dataclasses.replace(tables, unsafe_count=charged)


def measurement_is_inert(
    tables: RaceTables, model: MeasurementModel, tol: float = 1e-12
) -> bool:
    """Whether the channel leaves every invasion threshold exactly unchanged.

    The channel is inert exactly when the difference between the measured and
    the true charge base is column-constant, which for the affine family means
    ``gain = 1`` and ``attribution = 0``; the offset may be anything.  A gain
    other than one rescales the liability axis and is therefore *not* inert in
    this sense, even though it deforms nothing.
    """
    m = np.asarray(tables.unsafe_count, dtype=float)
    delta = (model.gain - 1.0) * m + model.attribution * m.T + model.offset
    return bool(np.all(np.abs(delta - delta[0, :][None, :]) <= tol))


def attribution_thresholds(tables: RaceTables, q: float) -> dict[str, float]:
    """The four thresholds of the paper under misattribution weight ``q``.

    Every threshold is still ``delta a / delta hat m`` because the selection
    functional is still affine in ``L``; only the denominator changes.  The
    entry ``window`` is the multiplicative width of the bistable window, the
    quantity the misattribution result is about.
    """
    from .theory import guard_invasion_threshold, invasion_threshold, safe_face_barrier

    tq = measured_tables(tables, MeasurementModel.misattribution(float(q)))
    guard = guard_invasion_threshold(tq)
    upper = invasion_threshold(tq, "CAS", "AS").critical_liability
    entry = invasion_threshold(tq, "CAS", "CS").critical_liability
    return {
        "q": float(q),
        "guard": float(guard),
        "CAS_into_AS": float(upper) if upper is not None else float("inf"),
        "CAS_into_CS": float(entry) if entry is not None else float("inf"),
        "barrier_AS": float(safe_face_barrier(tq, 0.0)),
        "barrier_CS": float(safe_face_barrier(tq, 1.0)),
        "window": float(upper / guard) if upper is not None and guard > 0 else float("inf"),
    }


def delayed_replicator(
    payoff_current: np.ndarray,
    charge: np.ndarray,
    liability: float,
    x0: np.ndarray,
    tau: float,
    t_end: float = 2000.0,
    dt: float = 0.01,
) -> np.ndarray:
    """Replicator flow in which the charge is levied on a lagged composition.

    The principal settles claims on an incident window that closed ``tau`` time
    units ago, so the fitness of design ``i`` at time ``t`` is

    .. math::
        f_i(t) = \\sum_j x_j(t)\\, a(i, j) - L \\sum_j x_j(t - \\tau)\\, m(i, j).

    Any rest point of the undelayed flow is a rest point of this one, because a
    constant history equals the current state; the delay can therefore change
    which attractor is reached and how, but not where the attractors are.  The
    integration is an explicit Euler scheme with a ring buffer for the history,
    which is constant and equal to ``x0`` on ``[-tau, 0]``.
    """
    a = np.asarray(payoff_current, dtype=float)
    m = np.asarray(charge, dtype=float)
    x = np.asarray(x0, dtype=float).copy()
    x = x / x.sum()

    n_lag = max(int(round(tau / dt)), 1)
    history = [x.copy() for _ in range(n_lag)]
    n_steps = int(round(t_end / dt))

    for _ in range(n_steps):
        x_lag = history[0]
        fitness = a @ x - float(liability) * (m @ x_lag)
        mean = float(x @ fitness)
        x = x + dt * x * (fitness - mean)
        np.clip(x, 0.0, None, out=x)
        total = x.sum()
        if total <= 0.0:
            break
        x /= total
        history.pop(0)
        history.append(x.copy())
    return x
