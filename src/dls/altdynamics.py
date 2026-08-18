"""Selection dynamics other than the replicator equation.

Every structural result of the paper is a statement about the *sign* of a
payoff difference under the selection functional, so it is inherited by any
dynamics whose rest points and their stability are governed by those signs.
This module implements three dynamics that are not payoff-monotone in the
replicator sense, so that the claim can be tested rather than asserted:

``logit``
    perturbed best response, ``xdot = softmax(beta * M x) - x``.  As
    ``beta -> inf`` it approaches the best-response dynamics; at finite
    ``beta`` it keeps every design at positive frequency.

``best_response``
    best response with inertia, ``xdot = BR(x) - x``, with ties split evenly.

``aspiration``
    aspiration-driven switching: an individual playing ``i`` is dissatisfied at
    rate ``1 / (1 + exp(beta (f_i - alpha)))`` for an aspiration level
    ``alpha`` and then adopts a uniformly random alternative.  Nobody imitates
    anybody, so this dynamics is not payoff-monotone and provides the sharpest
    test of the results.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

__all__ = [
    "logit_field",
    "best_response_field",
    "aspiration_field",
    "integrate_field",
    "attractor",
    "basin_average_unsafe",
]


def _normalise(x: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(x, dtype=float), 0.0, None)
    total = x.sum()
    return x / total if total > 0 else np.full(x.size, 1.0 / x.size)


def logit_field(x: np.ndarray, payoff: np.ndarray, beta: float = 1.0) -> np.ndarray:
    """Perturbed best-response (logit) field."""
    x = _normalise(x)
    f = payoff @ x
    z = beta * (f - f.max())
    p = np.exp(z)
    p /= p.sum()
    return p - x


def best_response_field(x: np.ndarray, payoff: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Best-response-with-inertia field; ties are split evenly."""
    x = _normalise(x)
    f = payoff @ x
    best = f >= f.max() - tol
    br = best.astype(float) / best.sum()
    return br - x


def aspiration_field(
    x: np.ndarray, payoff: np.ndarray, aspiration: float, beta: float = 1.0
) -> np.ndarray:
    """Aspiration-driven switching field.

    ``xdot_i = -x_i g_i + (1 / (n - 1)) sum_{j != i} x_j g_j`` with
    ``g_i = 1 / (1 + exp(beta (f_i - alpha)))`` the probability that an
    individual playing ``i`` is dissatisfied.
    """
    x = _normalise(x)
    n = x.size
    f = payoff @ x
    g = 1.0 / (1.0 + np.exp(beta * (f - aspiration)))
    outflow = x * g
    return -outflow + (outflow.sum() - outflow) / (n - 1)


def integrate_field(
    field, x0: np.ndarray, t_end: float = 500.0, rtol: float = 1e-9, atol: float = 1e-11
) -> np.ndarray:
    """Integrate a smooth simplex field from ``x0`` and return the end state."""

    def rhs(_t, x):
        return field(_normalise(x))

    sol = solve_ivp(
        rhs, (0.0, t_end), np.asarray(x0, dtype=float), rtol=rtol, atol=atol, method="RK45"
    )
    return _normalise(sol.y[:, -1])


def integrate_field_euler(
    field, x0: np.ndarray, t_end: float = 80.0, dt: float = 0.01
) -> np.ndarray:
    """Fixed-step integration, used for fields that are not continuous.

    The best-response field jumps across the boundaries between best-response
    regions, which defeats adaptive step-size control; along any interval on
    which the best reply is constant the flow is the linear contraction
    ``x(t) = BR + (x(0) - BR) e^{-t}``, so a fixed step is both stable and
    accurate here.
    """
    x = _normalise(x0)
    for _ in range(int(t_end / dt)):
        x = _normalise(x + dt * field(x))
    return x


def attractor(
    payoff: np.ndarray,
    x0: np.ndarray,
    kind: str = "logit",
    beta: float = 1.0,
    aspiration: float | None = None,
    t_end: float = 500.0,
) -> np.ndarray:
    """End state of one of the alternative dynamics started at ``x0``."""
    payoff = np.asarray(payoff, dtype=float)
    if kind == "logit":
        field = lambda x: logit_field(x, payoff, beta)          # noqa: E731
    elif kind == "best_response":
        field = lambda x: best_response_field(x, payoff)        # noqa: E731
        return integrate_field_euler(field, x0)
    elif kind == "aspiration":
        if aspiration is None:
            raise ValueError("aspiration dynamics needs an aspiration level")
        field = lambda x: aspiration_field(x, payoff, aspiration, beta)  # noqa: E731
    else:
        raise ValueError("unknown dynamics %r" % kind)
    return integrate_field(field, x0, t_end=t_end)


def basin_average_unsafe(
    payoff: np.ndarray,
    unsafe: np.ndarray,
    kind: str = "logit",
    beta: float = 1.0,
    aspiration: float | None = None,
    n_starts: int = 60,
    seed: int = 20260818,
    t_end: float = 2000.0,
) -> tuple[float, float]:
    """Basin-averaged Unsafe frequency and its spread across initial conditions."""
    rng = np.random.default_rng(seed)
    n = payoff.shape[0]
    values = np.empty(n_starts)
    for k in range(n_starts):
        x = attractor(
            payoff,
            rng.dirichlet(np.ones(n)),
            kind=kind,
            beta=beta,
            aspiration=aspiration,
            t_end=t_end,
        )
        values[k] = x @ unsafe @ x
    return float(values.mean()), float(values.std())
