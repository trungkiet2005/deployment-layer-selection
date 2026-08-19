"""Round-4 revision analyses: imperfect attribution, assortment, and the rate
at which the neutral safe face stops being neutral.

Writes ``results/round4.json``.  Every number quoted in the round-4 revision
that is not already in ``results/key_numbers.json``,
``results/robustness_summary.json`` or ``results/extensions.json`` is produced
here.

    python scripts/run_round4.py
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import numpy as np

from dls import RaceParams, build_race_tables
from dls.assortment import assorted_tables, assortment_thresholds, closing_assortment
from dls.dynamics import replicator_attractor
from dls.noisy import REDUCED_DESIGNS, build_noisy_tables, generous, grim, punisher
from dls.observation import (
    MeasurementModel,
    attribution_thresholds,
    delayed_replicator,
    measured_tables,
    measurement_is_inert,
)
from dls.probes import probe_scores, separating_probe_sets
from dls.theory import guard_invasion_threshold, invasion_threshold

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_extensions import L_GRID, replicator_curve, valley_depth  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

POOL = ("AS", "CS", "CAS")

#: liability grid wide enough to contain the upper edge at the largest
#: misattribution weight examined, ``42.77 / (1 - 0.5) = 85.5``
L_GRID_WIDE = np.unique(
    np.concatenate(
        [
            np.linspace(0.0, 1.0, 6),
            np.linspace(1.5, 8.0, 14),
            np.linspace(9.0, 20.0, 12),
            np.linspace(22.0, 60.0, 13),
            np.linspace(65.0, 130.0, 14),
        ]
    )
)

Q_VALUES = (0.0, 0.1, 0.25, 0.5)
R_VALUES = (0.0, 0.05, 0.1, 0.2, 0.3, 0.4)
ETA_FINE = (1e-4, 2.5e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2)


# --------------------------------------------------------------------------
# 1. what the principal can see
# --------------------------------------------------------------------------


def attribution_analysis(tables) -> dict:
    """Thresholds and long-run harm under an imperfect measurement channel."""
    out: dict = {"inertness": {}, "sweep": [], "curves": {}}

    base = {
        "guard": guard_invasion_threshold(tables),
        "CAS_into_AS": float(invasion_threshold(tables, "CAS", "AS").critical_liability),
    }

    # a constant offset is exactly inert; a gain is an exact rescaling of L
    off = measured_tables(tables, MeasurementModel(offset=3.0))
    gain = measured_tables(tables, MeasurementModel(gain=0.5))
    out["inertness"]["offset"] = {
        "column_constant": measurement_is_inert(tables, MeasurementModel(offset=3.0)),
        "guard": guard_invasion_threshold(off),
        "guard_error": abs(guard_invasion_threshold(off) - base["guard"]),
        "CAS_into_AS": float(invasion_threshold(off, "CAS", "AS").critical_liability),
    }
    out["inertness"]["gain"] = {
        "alpha": 0.5,
        "guard": guard_invasion_threshold(gain),
        "rescaling_error": abs(
            guard_invasion_threshold(gain) - base["guard"] / 0.5
        ),
        "CAS_into_AS": float(invasion_threshold(gain, "CAS", "AS").critical_liability),
    }

    # zero-mean measurement error: the selection functional sees the mean
    rng = np.random.default_rng(20260818)
    model = MeasurementModel(noise_scale=1.0)
    draws = []
    for n_draws in (1, 10, 100, 1000, 10000):
        acc = np.zeros_like(tables.unsafe_count)
        for _ in range(n_draws):
            acc += measured_tables(tables, model, rng=rng).unsafe_count
        acc /= n_draws
        avg = dataclasses.replace(tables, unsafe_count=acc)
        draws.append(
            {
                "n_draws": n_draws,
                "guard": guard_invasion_threshold(avg),
                "abs_error": abs(guard_invasion_threshold(avg) - base["guard"]),
            }
        )
    out["inertness"]["zero_mean_noise"] = {"sigma": 1.0, "draws": draws}

    # misattribution: the one channel that deforms
    for q in np.round(np.arange(0.0, 0.951, 0.05), 3):
        out["sweep"].append(attribution_thresholds(tables, float(q)))

    for q in Q_VALUES:
        t0 = time.time()
        tq = measured_tables(tables, MeasurementModel.misattribution(q))
        curve, spread = replicator_curve(tq, POOL, L_GRID_WIDE, n_starts=48)
        thr = attribution_thresholds(tables, q)
        out["curves"]["%.2f" % q] = {
            "q": q,
            "curve": [float(v) for v in curve],
            "max_spread": float(spread.max()),
            "valley": valley_depth(L_GRID_WIDE, curve),
            **thr,
        }
        print(
            "  q=%.2f  Ldagger=%.3f  upper=%.2f  window=%.2f  depth=%.4f  (%.0fs)"
            % (q, thr["guard"], thr["CAS_into_AS"], thr["window"],
               out["curves"]["%.2f" % q]["valley"]["depth"], time.time() - t0)
        )

    out["grid"] = [float(v) for v in L_GRID_WIDE]
    out["baseline"] = base
    return out


# --------------------------------------------------------------------------
# 2. assortative matching
# --------------------------------------------------------------------------


def assortment_analysis(tables) -> dict:
    """Thresholds and long-run harm in an assorted population."""
    out: dict = {"sweep": [], "curves": {}}
    for r in np.round(np.arange(0.0, 0.601, 0.025), 4):
        out["sweep"].append(assortment_thresholds(tables, float(r)))

    out["closing_r"] = closing_assortment(tables)
    out["guard_invariance"] = {
        "values": [assortment_thresholds(tables, r)["guard"] for r in R_VALUES],
        "max_deviation": float(
            max(
                abs(assortment_thresholds(tables, r)["guard"]
                    - guard_invasion_threshold(tables))
                for r in R_VALUES
            )
        ),
    }
    # the assortment level at which conditional safety needs no liability
    zero_r = None
    for r in np.linspace(0.0, 0.3, 3001):
        if assortment_thresholds(tables, float(r))["barrier_CS"] <= 0.0:
            zero_r = float(r)
            break
    out["free_protection_CS_r"] = zero_r

    grid = L_GRID
    for r in R_VALUES:
        t0 = time.time()
        tr = assorted_tables(tables, r)
        curve, spread = replicator_curve(tr, POOL, grid, n_starts=48)
        thr = assortment_thresholds(tables, r)
        out["curves"]["%.3f" % r] = {
            "r": r,
            "curve": [float(v) for v in curve],
            "max_spread": float(spread.max()),
            "valley": valley_depth(grid, curve),
            **thr,
        }
        print(
            "  r=%.3f  Ldagger=%.4f  upper=%.3f  window=%.2f  depth=%.4f  (%.0fs)"
            % (r, thr["guard"], thr["CAS_into_AS"], thr["window"],
               out["curves"]["%.3f" % r]["valley"]["depth"], time.time() - t0)
        )
    out["grid"] = [float(v) for v in grid]
    return out


# --------------------------------------------------------------------------
# 3. how fast neutrality breaks
# --------------------------------------------------------------------------


def face_perturbation_analysis() -> dict:
    """First-order rate at which execution noise destroys twinning."""
    rows = []
    for eta in ETA_FINE:
        tab = build_noisy_tables(eta=eta)
        i_as, i_cs = tab.strategies.index("AS"), tab.strategies.index("CS")
        da = float(tab.payoff[i_cs, i_as] - tab.payoff[i_as, i_as])
        dm = float(tab.unsafe_count[i_cs, i_as] - tab.unsafe_count[i_as, i_as])
        rows.append(
            {
                "eta": float(eta),
                "delta_a": da,
                "delta_m": dm,
                "delta_a_over_eta": da / eta,
                "delta_m_over_eta": dm / eta,
                "flip_liability": da / dm if abs(dm) > 1e-15 else None,
            }
        )
    # first-order coefficients by Richardson extrapolation on the two smallest eta
    e1, e2 = rows[0], rows[1]
    slope_a = (e2["delta_a_over_eta"] * e1["eta"] - e1["delta_a_over_eta"] * e2["eta"]) / (
        e1["eta"] - e2["eta"]
    )
    slope_m = (e2["delta_m_over_eta"] * e1["eta"] - e1["delta_m_over_eta"] * e2["eta"]) / (
        e1["eta"] - e2["eta"]
    )
    # crossing time of the face under the induced gradient, from x = 0.05 to 0.95
    span = float(np.log(0.95 / 0.05) - np.log(0.05 / 0.95))
    crossing = {}
    for eta in (1e-3, 1e-2, 5e-2):
        for L in (0.0, 4.27, 10.0):
            g = eta * (slope_a - L * slope_m)
            crossing["eta=%.3f,L=%.2f" % (eta, L)] = {
                "gradient": float(g),
                "crossing_time": float(span / g) if g > 0 else None,
            }
    return {
        "rows": rows,
        "slope_a": float(slope_a),
        "slope_m": float(slope_m),
        "flip_liability_limit": float(slope_a / slope_m),
        "expected_horizon_minus_one": float(RaceParams().expected_horizon - 1.0),
        "crossing": crossing,
        "drift_dominates_below_eta": {
            "beta": 0.05,
            "Z": 100,
            "L": 0.0,
            "eta_star": float(1.0 / (0.05 * 100 * slope_a)),
        },
    }


# --------------------------------------------------------------------------
# 4. probes under execution noise
# --------------------------------------------------------------------------


def probe_noise_analysis() -> dict:
    """Separating margin of the recommended probe as execution noise rises."""
    rows = []
    for eta in (0.0, 0.005, 0.01, 0.02, 0.05, 0.10):
        tab = build_noisy_tables(eta=eta)
        sets = separating_probe_sets(tab, target_pool=("AS", "CS"), max_size=4)
        scores_cs = probe_scores(tab, ("CS",))
        scores_as = probe_scores(tab, ("AS",))
        margin_cs = min(scores_cs["AU"], scores_cs["CAS"]) - max(
            scores_cs["AS"], scores_cs["CS"]
        )
        margin_as = min(scores_as["AU"], scores_as["CAS"]) - max(
            scores_as["AS"], scores_as["CS"]
        )
        best = max(sets, key=lambda s: s[2] - s[1]) if sets else None
        rows.append(
            {
                "eta": float(eta),
                "margin_reciprocating": float(margin_cs),
                "margin_solo": float(margin_as),
                "u_CS_self": float(tab.unsafe_frequency[tab.strategies.index("CS"),
                                                        tab.strategies.index("CS")]),
                "n_separating_sets": len(sets),
                "best_set": list(best[0]) if best else None,
                "best_margin": float(best[2] - best[1]) if best else None,
                "episodes_reciprocating": int(np.ceil((1.386 / margin_cs) ** 2))
                if margin_cs > 0
                else None,
                "episodes_solo": int(np.ceil((1.386 / margin_as) ** 2))
                if margin_as > 0
                else None,
            }
        )
        print(
            "  eta=%.3f  reciprocating margin=%.4f (n>=%s)  solo margin=%.4f (n>=%s)"
            % (eta, margin_cs, rows[-1]["episodes_reciprocating"], margin_as,
               rows[-1]["episodes_solo"])
        )
    return {"rows": rows, "confidence": "95% two-sided, Bernoulli bound sd <= 0.5"}


# --------------------------------------------------------------------------
# 5. a grim trigger in the pool
# --------------------------------------------------------------------------


def grim_pool_analysis() -> dict:
    """Enlarged pools containing a never-forgiving conditional design."""
    pools = {
        "baseline": {k: REDUCED_DESIGNS[k] for k in POOL},
        "with_grim": {**{k: REDUCED_DESIGNS[k] for k in POOL}, "GRIM": grim(0.0)},
        "with_grim_and_generous": {
            **{k: REDUCED_DESIGNS[k] for k in POOL},
            "GRIM": grim(0.0),
            "GCS": generous("CS", 0.25),
        },
        "with_grim_and_punisher": {
            **{k: REDUCED_DESIGNS[k] for k in POOL},
            "GRIM": grim(0.0),
            "PUN2": punisher(2),
        },
    }
    grid = L_GRID
    out = {}
    for eta in (0.0, 0.01, 0.05):
        for name, designs in pools.items():
            t0 = time.time()
            tab = build_noisy_tables(designs=designs, eta=eta)
            pool = tuple(tab.strategies)
            curve, _ = replicator_curve(tab, pool, grid, n_starts=48)
            guard = guard_invasion_threshold(tab)
            upper = invasion_threshold(tab, "CAS", "AS").critical_liability
            key = "%s@eta=%.3f" % (name, eta)
            out[key] = {
                "pool": list(pool),
                "eta": float(eta),
                "guard": float(guard),
                "CAS_into_AS": float(upper) if upper is not None else None,
                "window": float(upper / guard) if upper and guard > 0 else None,
                "valley": valley_depth(grid, curve),
                "u_GRIM_self": float(
                    tab.unsafe_frequency[pool.index("GRIM"), pool.index("GRIM")]
                )
                if "GRIM" in pool
                else None,
                "curve": [float(v) for v in curve],
            }
            print(
                "  %-32s Ldagger=%.3f  window=%s  depth=%.4f  (%.0fs)"
                % (key, guard,
                   "%.2f" % out[key]["window"] if out[key]["window"] else "n/a",
                   out[key]["valley"]["depth"], time.time() - t0)
            )
    out["grid"] = [float(v) for v in grid]
    return out


# --------------------------------------------------------------------------
# 6. lagged enforcement
# --------------------------------------------------------------------------


def lag_analysis(tables) -> dict:
    """Basin composition when the charge is levied on a lagged composition.

    Time is normalised so that the largest fitness difference in the selection
    functional is one, which makes the lag comparable with the relaxation time
    of the undelayed flow.
    """
    idx = [tables.strategies.index(s) for s in POOL]
    sel = np.ix_(idx, idx)
    a, m, u = tables.payoff[sel], tables.unsafe_count[sel], tables.unsafe_frequency[sel]

    rng = np.random.default_rng(20260818)
    starts = [rng.dirichlet(np.ones(len(POOL))) for _ in range(24)]

    out = {"rows": []}
    for liability in (6.0, 10.0, 20.0):
        scale = float(np.ptp(a - liability * m))
        a_n, m_n = a / scale, m / scale
        for tau in (0.0, 1.0, 5.0, 20.0):
            vals = []
            for x0 in starts:
                if tau == 0.0:
                    x = replicator_attractor(a - liability * m, x0)
                else:
                    x = delayed_replicator(
                        a_n, m_n, liability, x0, tau=tau, t_end=300.0, dt=0.02
                    )
                vals.append(float(x @ u @ x))
            vals = np.array(vals)
            out["rows"].append(
                {
                    "L": float(liability),
                    "tau": float(tau),
                    "mean_unsafe": float(vals.mean()),
                    "unsafe_basin_share": float((vals > 0.05).mean()),
                    "payoff_scale": scale,
                }
            )
            print(
                "  L=%5.1f tau=%5.1f  mean U=%.4f  unsafe basin=%.3f"
                % (liability, tau, vals.mean(), (vals > 0.05).mean())
            )
    return out


# --------------------------------------------------------------------------


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    tables = build_race_tables(RaceParams())
    payload: dict = {}

    print("1. imperfect attribution")
    payload["attribution"] = attribution_analysis(tables)
    print("2. assortative matching")
    payload["assortment"] = assortment_analysis(tables)
    print("3. how fast neutrality breaks")
    payload["face_perturbation"] = face_perturbation_analysis()
    print("4. probes under execution noise")
    payload["probe_noise"] = probe_noise_analysis()
    print("5. a grim trigger in the pool")
    payload["grim_pool"] = grim_pool_analysis()
    print("6. lagged enforcement")
    payload["lag"] = lag_analysis(tables)

    path = RESULTS / "round4.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
