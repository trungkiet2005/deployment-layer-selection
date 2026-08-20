"""Round-3 revision analyses: noise, richer designs, alternative dynamics,
non-linear charges, adversarial probes and the generality of the ratchet.

Writes ``results/extensions.json``.  Every number quoted in the revision that
is not already in ``results/key_numbers.json`` or
``results/robustness_summary.json`` is produced here.

    python scripts/run_extensions.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from dls import RaceParams, build_race_tables
from dls.altdynamics import basin_average_unsafe
from dls.charges import CHANNELS, charge_thresholds, charged_matrices
from dls.dynamics import replicator_attractor
from dls.functionals import build_selection_matrix
from dls.noisy import REDUCED_DESIGNS, build_noisy_tables, generous, punisher
from dls.probes import probe_scores, separating_probe_sets
from dls.race import RaceTables
from dls.ratchet import RatchetParams, hysteresis_sweep
from dls.theory import (
    guard_invasion_threshold,
    invasion_threshold,
    safe_face_barrier,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

L_GRID = np.unique(
    np.concatenate(
        [
            np.linspace(0.0, 1.0, 6),
            np.linspace(1.5, 8.0, 14),
            np.linspace(9.0, 20.0, 12),
            np.linspace(22.0, 60.0, 13),
        ]
    )
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _subset(tables: RaceTables, pool: tuple[str, ...]) -> tuple[np.ndarray, ...]:
    idx = [tables.strategies.index(s) for s in pool]
    sel = np.ix_(idx, idx)
    return tables.payoff[sel], tables.unsafe_count[sel], tables.unsafe_frequency[sel]


def replicator_curve(
    tables: RaceTables,
    pool: tuple[str, ...],
    liabilities: np.ndarray,
    n_starts: int = 48,
    seed: int = 20260818,
) -> tuple[np.ndarray, np.ndarray]:
    """Basin-averaged Unsafe frequency and its spread over a liability grid."""
    a, m, u = _subset(tables, pool)
    rng = np.random.default_rng(seed)
    starts = [rng.dirichlet(np.ones(len(pool))) for _ in range(n_starts)]
    mean = np.empty(liabilities.size)
    spread = np.empty(liabilities.size)
    for k, lam in enumerate(liabilities):
        payoff = a - lam * m
        vals = np.array(
            [
                (lambda x: float(x @ u @ x))(replicator_attractor(payoff, x0))
                for x0 in starts
            ]
        )
        mean[k], spread[k] = vals.mean(), vals.std()
    return mean, spread


def valley_depth(liabilities: np.ndarray, curve: np.ndarray, l_min: float = 1.0) -> dict:
    """Largest increase of long-run harm along the liability axis above ``l_min``.

    A liability valley is present exactly when this is positive: some pair
    ``L1 < L2`` has ``U(L2) > U(L1)``, i.e. raising liability raises harm.
    """
    mask = liabilities >= l_min
    ls, cs = liabilities[mask], curve[mask]
    best = 0.0
    arg = (float("nan"), float("nan"))
    running_min, running_arg = cs[0], ls[0]
    for lam, val in zip(ls, cs):
        if val - running_min > best:
            best = float(val - running_min)
            arg = (float(running_arg), float(lam))
        if val < running_min:
            running_min, running_arg = val, lam
    return {"depth": best, "from_L": arg[0], "to_L": arg[1]}


# --------------------------------------------------------------------------
# 1. execution noise in the reduced pool
# --------------------------------------------------------------------------


def noise_analysis(etas=(0.0, 0.01, 0.02, 0.05, 0.075, 0.10, 0.15, 0.20)) -> dict:
    out = {}
    for eta in etas:
        t = time.time()
        tab = build_noisy_tables(eta=eta)
        curve, spread = replicator_curve(tab, ("AS", "CS", "CAS"), L_GRID)
        guard = guard_invasion_threshold(tab)
        upper = invasion_threshold(tab, "CAS", "AS").critical_liability
        entry = invasion_threshold(tab, "CAS", "CS").critical_liability
        # gradient on the safe face: growth of a rare CS in an AS resident
        i_as, i_cs = tab.strategies.index("AS"), tab.strategies.index("CS")
        da_face = float(tab.payoff[i_cs, i_as] - tab.payoff[i_as, i_as])
        dm_face = float(tab.unsafe_count[i_cs, i_as] - tab.unsafe_count[i_as, i_as])
        out["%.4f" % eta] = {
            "eta": float(eta),
            "guard_threshold": float(guard),
            "L_CAS_into_AS": float(upper),
            "L_CAS_into_CS": float(entry),
            "window_width": float(upper / guard) if guard > 0 else None,
            "barrier_ratio": float(
                safe_face_barrier(tab, 0.0) / safe_face_barrier(tab, 1.0)
            ),
            "solo_score_CS": float(tab.unsafe_frequency[i_cs, i_as]),
            "solo_score_CAS": float(
                tab.unsafe_frequency[tab.strategies.index("CAS"), i_as]
            ),
            "u_self_AS": float(tab.unsafe_frequency[i_as, i_as]),
            "u_self_CS": float(tab.unsafe_frequency[i_cs, i_cs]),
            "face_gradient_da": da_face,
            "face_gradient_dm": dm_face,
            "face_flip_L": float(da_face / dm_face) if abs(dm_face) > 1e-12 else None,
            "valley": valley_depth(L_GRID, curve),
            "max_spread": float(spread.max()),
            "curve": [float(v) for v in curve],
            "seconds": round(time.time() - t, 1),
        }
        print(
            "  eta=%.3f  Ldagger=%.3f  window=%.2f  valley depth=%.4f"
            % (eta, guard, out["%.4f" % eta]["window_width"], out["%.4f" % eta]["valley"]["depth"])
        )
    return out


# --------------------------------------------------------------------------
# 2. richer design pools
# --------------------------------------------------------------------------


def pool_analysis(etas=(0.0, 0.02)) -> dict:
    pools = {
        "baseline": ("AS", "CS", "CAS"),
        "plus_generous_guard": ("AS", "CS", "CAS", "GCS"),
        "plus_harsh_guard": ("AS", "CS", "CAS", "PUN2"),
        "plus_generous_aggressor": ("AS", "CS", "CAS", "GCAS"),
        "full": ("AS", "CS", "CAS", "GCS", "PUN2", "GCAS"),
    }
    designs = dict(REDUCED_DESIGNS)
    designs["GCS"] = generous("CS", 0.25)
    designs["GCAS"] = generous("CAS", 0.25)
    designs["PUN2"] = punisher(2)

    out = {}
    for eta in etas:
        tab = build_noisy_tables(designs, eta=eta)
        idx = {s: k for k, s in enumerate(tab.strategies)}
        # weak dominance of CAS over AU under noise, at three liability levels
        dominance = {}
        for lam in (0.0, 5.0, 40.0):
            M = build_selection_matrix(tab, lam)
            gaps = M[idx["CAS"], :] - M[idx["AU"], :]
            dominance["%.0f" % lam] = {
                "min_gap": float(gaps.min()),
                "gaps": {s: float(gaps[k]) for k, s in enumerate(tab.strategies)},
            }
        entry = {"dominance_CAS_over_AU": dominance, "pools": {}}
        for label, pool in pools.items():
            curve, spread = replicator_curve(tab, pool, L_GRID)
            entry["pools"][label] = {
                "pool": list(pool),
                "valley": valley_depth(L_GRID, curve),
                "U_at_L0": float(curve[0]),
                "U_min": float(curve.min()),
                "U_at_L60": float(curve[-1]),
                "max_spread": float(spread.max()),
                "curve": [float(v) for v in curve],
            }
            print(
                "  eta=%.2f %-24s valley depth=%.4f  (U: %.3f -> %.3f)"
                % (eta, label, entry["pools"][label]["valley"]["depth"], curve[0], curve[-1])
            )
        out["%.4f" % eta] = entry
    return out


# --------------------------------------------------------------------------
# 3. alternative selection dynamics
# --------------------------------------------------------------------------


def dynamics_analysis() -> dict:
    tables = build_race_tables(RaceParams())
    a, m, u = _subset(tables, ("AS", "CS", "CAS"))
    grid = np.array([0.0, 0.3, 0.6, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 7.0, 10.0, 15.0,
                     20.0, 30.0, 42.0, 45.0, 55.0])
    specs = {
        "replicator": dict(kind=None),
        "logit_beta1": dict(kind="logit", beta=1.0),
        "logit_beta10": dict(kind="logit", beta=10.0),
        "best_response": dict(kind="best_response"),
        "aspiration_low": dict(kind="aspiration", beta=0.5, aspiration=30.0),
        "aspiration_high": dict(kind="aspiration", beta=0.5, aspiration=55.0),
    }
    out = {}
    for label, spec in specs.items():
        curve = np.empty(grid.size)
        spread = np.empty(grid.size)
        for k, lam in enumerate(grid):
            payoff = a - lam * m
            if spec["kind"] is None:
                rng = np.random.default_rng(20260818)
                vals = np.array(
                    [
                        float((lambda x: x @ u @ x)(replicator_attractor(payoff, x0)))
                        for x0 in (rng.dirichlet(np.ones(3)) for _ in range(60))
                    ]
                )
                curve[k], spread[k] = vals.mean(), vals.std()
            else:
                curve[k], spread[k] = basin_average_unsafe(
                    payoff,
                    u,
                    kind=spec["kind"],
                    beta=spec.get("beta", 1.0),
                    aspiration=spec.get("aspiration"),
                    n_starts=48,
                )
        out[label] = {
            "liabilities": [float(v) for v in grid],
            "curve": [float(v) for v in curve],
            "spread": [float(v) for v in spread],
            "valley": valley_depth(grid, curve),
            "max_spread": float(spread.max()),
        }
        print(
            "  %-18s valley depth=%.4f on (%.2f, %.2f), max spread %.3f"
            % (
                label,
                out[label]["valley"]["depth"],
                out[label]["valley"]["from_L"],
                out[label]["valley"]["to_L"],
                spread.max(),
            )
        )
    return out


# --------------------------------------------------------------------------
# 4. non-linear charges
# --------------------------------------------------------------------------


def charge_analysis() -> dict:
    tables = build_race_tables(RaceParams())
    out = {}
    for name in CHANNELS:
        thr = charge_thresholds(tables, name)
        a, _, u = _subset(tables, ("AS", "CS", "CAS"))
        idx = [tables.strategies.index(s) for s in ("AS", "CS", "CAS")]
        rng = np.random.default_rng(20260818)
        starts = [rng.dirichlet(np.ones(3)) for _ in range(48)]
        # Valley depth is a largest-increase-over-a-grid statistic, so it is
        # only comparable across sections when the grid, the number of starts
        # and the lower cut are the same.  Use L_GRID, as the noise and
        # assortment sweeps do, extended to the range the convex charge needs:
        # its upper edge sits at L = 384.9, well beyond the common grid.
        grid = np.unique(np.concatenate([L_GRID, np.geomspace(60.0, 600.0, 12)]))
        curve = np.empty(grid.size)
        for k, lam in enumerate(grid):
            payoff = charged_matrices(tables, name, lam)[np.ix_(idx, idx)]
            vals = [
                float((lambda x: x @ u @ x)(replicator_attractor(payoff, x0)))
                for x0 in starts
            ]
            curve[k] = float(np.mean(vals))
        window = (
            float(thr["CAS_into_AS"] / thr["guard"])
            if thr["guard"] > 0 and np.isfinite(thr["CAS_into_AS"])
            else None
        )
        out[name] = {
            "description": CHANNELS[name].description,
            "thresholds": thr,
            "window_width": window,
            "valley": valley_depth(grid, curve),
            "liabilities": [float(v) for v in grid],
            "curve": [float(v) for v in curve],
        }
        print(
            "  %-10s guard=%8.3f  upper=%8.3f  width=%s  valley depth=%.3f"
            % (
                name,
                thr["guard"],
                thr["CAS_into_AS"],
                ("%.2f" % window) if window else "--",
                out[name]["valley"]["depth"],
            )
        )
    return out


# --------------------------------------------------------------------------
# 5. adversarial probes
# --------------------------------------------------------------------------


def probe_analysis() -> dict:
    tables = build_race_tables(RaceParams())
    out = {"solo": probe_scores(tables, ("AS",))}
    out["adversarial"] = probe_scores(tables, ("AS", "CAS"))
    out["self_play"] = {
        s: float(tables.unsafe_frequency[k, k]) for k, s in enumerate(tables.strategies)
    }
    out["separating_sets"] = [
        {"probes": list(p), "epsilon_low": lo, "epsilon_high": hi}
        for p, lo, hi in separating_probe_sets(tables, ("AS", "CS"), max_size=2)
    ]
    # the same under execution noise: does the separation survive?
    noisy = {}
    for eta in (0.0, 0.02, 0.05, 0.10):
        tab = build_noisy_tables(eta=eta)
        sc = probe_scores(tab, ("AS", "CAS"))
        solo = probe_scores(tab, ("AS",))
        noisy["%.4f" % eta] = {
            "adversarial": sc,
            "solo": solo,
            "adversarial_gap": float(sc["CAS"] - sc["CS"]),
            "solo_gap": float(solo["CAS"] - solo["CS"]),
        }
    out["under_noise"] = noisy
    print("  solo scores:", {k: round(v, 4) for k, v in out["solo"].items()})
    print("  adversarial scores:", {k: round(v, 4) for k, v in out["adversarial"].items()})
    print("  separating probe sets:", [p["probes"] for p in out["separating_sets"]])
    return out


# --------------------------------------------------------------------------
# 6. generality of the ratchet
# --------------------------------------------------------------------------


def ratchet_analysis() -> dict:
    """Hysteresis width across erosion channels, residual fractions and speeds.

    The sweep protocol is the one of Figure~8: the descending branch starts in
    the protected regime with the ratchet variable at zero, so that diffusion
    is switched on only by the transition itself.  Mutation is kept at 1e-6 so
    that the protected branch carries no residual harm, which is the
    hypothesis of the hysteresis theorem.
    """
    tables = build_race_tables(RaceParams()).subset(("AS", "CS", "CAS"))
    grid = np.geomspace(0.12, 25.0, 70)
    protected = np.array([0.02, 0.96, 0.02])
    l_star = invasion_threshold(tables, "CAS", "CS").critical_liability
    tol = 1e-3
    out = {"L_star_CAS_into_CS": float(l_star)}
    configs = [
        ("linear_theta0.9_eps0.05", dict(channel="linear", theta=0.9, epsilon=0.05)),
        ("linear_theta0.9_eps0.01", dict(channel="linear", theta=0.9, epsilon=0.01)),
        ("linear_theta0.9_eps0.20", dict(channel="linear", theta=0.9, epsilon=0.20)),
        ("linear_theta0.5_eps0.05", dict(channel="linear", theta=0.5, epsilon=0.05)),
        ("saturating_kappa9_eps0.05", dict(channel="saturating", kappa=9.0, epsilon=0.05)),
        ("saturating_kappa1_eps0.05", dict(channel="saturating", kappa=1.0, epsilon=0.05)),
    ]
    for label, kwargs in configs:
        params = RatchetParams(mutation=1e-6, **kwargs)
        sweep = hysteresis_sweep(tables, params, grid, x0=protected, t_end=3000.0)
        lost = [float(l) for l, uu in zip(grid, sweep.unsafe_forward) if uu > tol]
        recovered = [float(l) for l, uu in zip(grid, sweep.unsafe_backward) if uu <= tol]
        l_down = max(lost) if lost else None
        l_up = min(recovered) if recovered else None
        out[label] = {
            "residual_fraction": params.residual_fraction,
            "predicted_L_down": float(l_star),
            "predicted_L_up": float(l_star / params.residual_fraction),
            "predicted_ratio": float(1.0 / params.residual_fraction),
            "L_down_numeric": l_down,
            "L_up_numeric": l_up,
            "observed_ratio": float(l_up / l_down) if (l_up and l_down) else None,
            "loop_area": sweep.loop_area,
        }
        print(
            "  %-28s rho=%.3f  L_down %s (pred %.3f)  L_up %s (pred %.3f)  ratio %s vs %.2f"
            % (
                label,
                params.residual_fraction,
                ("%.3f" % l_down) if l_down else "--",
                l_star,
                ("%.3f" % l_up) if l_up else "--",
                l_star / params.residual_fraction,
                ("%.2f" % out[label]["observed_ratio"]) if out[label]["observed_ratio"] else "--",
                out[label]["predicted_ratio"],
            )
        )

    # the protected branch is frozen only when U vanishes exactly; with
    # execution noise it does not, so the ratchet creeps
    creep = {}
    for eta in (0.0, 0.01, 0.02, 0.05):
        tab = build_noisy_tables(eta=eta)
        i_cs = tab.strategies.index("CS")
        u_safe = float(tab.unsafe_frequency[i_cs, i_cs])
        creep["%.4f" % eta] = {
            "U_on_protected_branch": u_safe,
            "z_halflife_in_1_over_epsilon": (
                float(np.log(2.0) / u_safe) if u_safe > 0 else None
            ),
        }
    out["protected_branch_creep"] = creep
    return out


# --------------------------------------------------------------------------


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    report: dict = {}

    print("[1/6] execution noise in the reduced pool")
    report["noise"] = noise_analysis()
    print("[2/6] richer design pools")
    report["pools"] = pool_analysis()
    print("[3/6] alternative selection dynamics")
    report["dynamics"] = dynamics_analysis()
    print("[4/6] non-linear liability charges")
    report["charges"] = charge_analysis()
    print("[5/6] adversarial probes")
    report["probes"] = probe_analysis()
    print("[6/6] generality of the ratchet")
    report["ratchet"] = ratchet_analysis()

    report["liability_grid"] = [float(v) for v in L_GRID]
    path = RESULTS / "extensions.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
