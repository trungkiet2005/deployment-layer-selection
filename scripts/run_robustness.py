"""Robustness checks requested by review: prize scale, risk treatment,
escape times, the second erosion channel, and the sensitivity of the filter
comparison to the seeded share of the filtered design.

Usage
-----
    python scripts/run_robustness.py [--outdir results]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from dls.dynamics import stationary_analysis
from dls.functionals import build_selection_matrix
from dls.plotting import (FS, PALETTE, fitted_legend, new_figure, panel_title, save,
                          use_paper_style)
from dls.race import RaceParams, build_race_tables
from dls.robustness import (
    hysteresis_width,
    mean_exit_time,
    threshold_grid,
    thresholds_for,
    unsafe_mass,
)
from dls.theory import evaluation_filter, face_equilibrium, matched_longrun_unsafe

POOL3 = ("AS", "CS", "CAS")
BASELINE_PRIZE = 100.0
BASELINE_P_MAX = 0.6


def prize_and_risk_sweep(outdir: Path) -> pd.DataFrame:
    prizes = np.array([10.0, 20.0, 50.0, 100.0, 200.0, 400.0])
    p_maxes = np.array([0.1, 0.3, 0.6, 0.9])
    rows = []
    for t in threshold_grid(prizes, p_maxes):
        rows.append(
            {
                "prize": t.prize,
                "p_max": t.p_max,
                "L_CAS_to_AS": t.l_cas_invades_as,
                "L_CAS_to_CS": t.l_cas_invades_cs,
                "L_guard": t.l_guard,
                "window_lo": t.window_lo,
                "window_hi": t.window_hi,
                "window_width": t.window_width,
                "barrier_ratio": t.barrier_ratio,
                **t.normalised(),
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(outdir / "tables" / "robustness_thresholds.csv", index=False)
    return df


def figure_robustness(df: pd.DataFrame, outdir: Path) -> None:
    fig, axes = new_figure(2.55, nrows=1, ncols=3)

    styles = {0.1: "-o", 0.3: "-s", 0.6: "-^", 0.9: "-d"}
    colours = {0.1: PALETTE["AS"], 0.3: PALETTE["CS"],
               0.6: PALETTE["accent"], 0.9: PALETTE["CAS"]}

    ax = axes[0]
    for p, sub in df.groupby("p_max"):
        sub = sub.sort_values("prize")
        ax.plot(sub["prize"], sub["L_CAS_to_AS"] / sub["prize"], styles[p], ms=3.4,
                color=colours[p], label=rf"$p_r^{{\max}}={p}$")
    ax.set_xscale("log")
    ax.set_xlabel(r"race prize $B$")
    ax.set_ylabel(r"$L^{*}_{\mathrm{CAS}\to\mathrm{AS}}/B$")
    panel_title(ax, "A", "protecting AS")
    fitted_legend(ax, ncol=2, columnspacing=0.7, handlelength=1.4)

    ax = axes[1]
    for p, sub in df.groupby("p_max"):
        sub = sub.sort_values("prize")
        if (sub["barrier_ratio"] <= 0).any():
            continue  # conditional safety needs no liability at all; see annotation
        ax.plot(sub["prize"], sub["barrier_ratio"], styles[p], ms=3.4,
                color=colours[p], label=rf"$p_r^{{\max}}={p}$")
    ax.axhline(1.0, color=PALETTE["neutral"], lw=0.7, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"race prize $B$")
    ax.set_ylabel(r"$L^{*}_{\mathrm{CAS}\to\mathrm{AS}}\,/\,L^{*}_{\mathrm{CAS}\to\mathrm{CS}}$")
    # chr(10) rather than an escape, so the source survives shell round-trips
    note = chr(10).join([
        r"at $p_r^{\max}=0.9$ the ratio is",
        r"undefined: $L^{*}_{\mathrm{CAS}\to\mathrm{CS}}<0$,",
        r"CS protected at zero liability",
    ])
    ax.text(10.5, 1.25, note, fontsize=FS["tiny"], color=PALETTE["CAS"],
            va="bottom")
    panel_title(ax, "B", "CS is cheaper")

    ax = axes[2]
    for p, sub in df.groupby("p_max"):
        sub = sub.sort_values("prize")
        ax.plot(sub["prize"], sub["window_width"], styles[p], ms=3.4,
                color=colours[p], label=rf"$p_r^{{\max}}={p}$")
    ax.axhline(1.0, color=PALETTE["neutral"], lw=0.7, ls="--")
    ax.text(11, 1.06, "no window", fontsize=FS["annot"], color=PALETTE["neutral"])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"race prize $B$")
    ax.set_ylabel(r"width of the bistability window")
    panel_title(ax, "C", "the valley across $B$")

    save(fig, outdir / "figures" / "fig09_robustness")


def escape_times(outdir: Path) -> pd.DataFrame:
    base = build_race_tables(RaceParams(p_max=BASELINE_P_MAX))
    sub = base.subset(POOL3)
    rows = []
    L = 10.0  # inside the bistability window
    eq = face_equilibrium(sub, "AS", "CAS", L)
    assert eq.fraction_second is not None
    pi_p = build_selection_matrix(sub, L)

    for Z in (30, 50, 80, 100):
        counts = np.zeros(3)
        counts[POOL3.index("CAS")] = round(eq.fraction_second * Z)
        counts[POOL3.index("AS")] = Z - counts[POOL3.index("CAS")]
        for beta in (0.02, 0.05, 0.2):
            mu = 1.0 / Z
            t = mean_exit_time(
                pi_p, Z, beta, mu, unsafe_index=POOL3.index("CAS"),
                start_counts=counts,
            )
            res = stationary_analysis(pi_p, sub.unsafe_frequency,
                                      population_size=Z, beta=beta, mu=mu)
            rows.append(
                {
                    "effective_liability": L,
                    "Z": Z,
                    "beta": beta,
                    "mu": mu,
                    "mean_exit_steps": t,
                    "mean_exit_generations": t / Z,
                    "stationary_unsafe_mass": unsafe_mass(
                        res.state_distribution, Z, 3, POOL3.index("CAS")
                    ),
                    "stationary_unsafe_frequency": res.unsafe_frequency,
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(outdir / "tables" / "escape_times.csv", index=False)
    return df


def seed_sensitivity(outdir: Path) -> pd.DataFrame:
    base = build_race_tables(RaceParams(p_max=BASELINE_P_MAX))
    full = evaluation_filter(base, 1.0)
    filtered = evaluation_filter(base, 0.2)
    rows = []
    for share in (0.01, 0.05, 0.10, 0.20, 0.35):
        for L in (0.0, 0.3, 1.0, 5.0, 10.0, 45.0):
            a = matched_longrun_unsafe(base, L, pool=full, extra_share=share, n_starts=80)
            b = matched_longrun_unsafe(base, L, pool=filtered, n_starts=80)
            rows.append({"seed_share": share, "effective_liability": L,
                         "unsafe_full": a, "unsafe_filtered": b, "gap": abs(a - b)})
    df = pd.DataFrame(rows)
    df.to_csv(outdir / "tables" / "seed_sensitivity.csv", index=False)
    return df


def main(outdir: Path) -> None:
    use_paper_style()
    (outdir / "tables").mkdir(parents=True, exist_ok=True)
    (outdir / "figures").mkdir(parents=True, exist_ok=True)

    print("prize and risk sweep ...")
    df = prize_and_risk_sweep(outdir)
    figure_robustness(df, outdir)

    print("escape times ...")
    esc = escape_times(outdir)

    print("seed sensitivity ...")
    seeds = seed_sensitivity(outdir)

    base_row = df[(df.prize == BASELINE_PRIZE) & (df.p_max == BASELINE_P_MAX)].iloc[0]
    summary = {
        "baseline": {k: float(base_row[k]) for k in
                     ["L_CAS_to_AS", "L_CAS_to_CS", "L_guard", "window_width",
                      "barrier_ratio", "L_CAS_to_AS_over_B", "L_CAS_to_CS_over_B"]},
        "window_exists_fraction": float((df.window_width > 1.0).mean()),
        "barrier_ratio_min": float(df.barrier_ratio.min()),
        "barrier_ratio_max": float(df.barrier_ratio.max()),
        "window_width_min": float(df.window_width[df.window_width > 1].min()),
        "window_width_max": float(df.window_width.max()),
        "hysteresis_width_linear_theta0.9": hysteresis_width(0.9, "linear"),
        "hysteresis_width_saturating_kappa9": hysteresis_width(0.0, "saturating", 9.0),
        "escape_generations_min": float(esc.mean_exit_generations.min()),
        "escape_generations_max": float(esc.mean_exit_generations.max()),
        "seed_sensitivity_max_gap": float(seeds.gap.max()),
    }
    (outdir / "robustness_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    main(parser.parse_args().outdir)
