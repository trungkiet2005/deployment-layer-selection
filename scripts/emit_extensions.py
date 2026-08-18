"""Turn ``results/extensions.json`` into the manuscript's tables and figure.

Writes ``results/tables/tab_noise.tex``, ``tab_charges.tex``,
``tab_hysteresis.tex`` and ``results/figures/fig10_generality.pdf``.

    python scripts/emit_extensions.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dls.plotting import (
    FIG_WIDTH,
    FS,
    PALETTE,
    fitted_legend,
    new_figure,
    panel_title,
    save,
    use_paper_style,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

DYNAMICS_LABEL = {
    "replicator": "replicator",
    "logit_beta10": r"logit, $\beta=10$",
    "logit_beta1": r"logit, $\beta=1$",
    "best_response": "best response",
    "aspiration_low": r"aspiration, $\alpha=30$",
    "aspiration_high": r"aspiration, $\alpha=55$",
}

CHANNEL_LABEL = {
    "linear": r"linear, $\varphi(m)=m$",
    "convex": r"convex, $\varphi\propto m^{2}$",
    "concave": r"concave, $\varphi\propto\sqrt{m}$",
    "capped": r"capped at $m=3$",
    "threshold": r"de minimis below $m=2$",
}


def _fmt(value, digits=3, inf="$\\infty$"):
    if value is None:
        return "--"
    if not np.isfinite(value):
        return inf
    return ("%%.%df" % digits) % value


def table_noise(ext: dict) -> str:
    rows = []
    for key in sorted(ext["noise"], key=float):
        v = ext["noise"][key]
        rows.append(
            "%.3f & %s & %s & %s & %s & %s & %s \\\\"
            % (
                v["eta"],
                _fmt(v["guard_threshold"], 2),
                _fmt(v["L_CAS_into_AS"], 2),
                _fmt(v["window_width"], 2),
                _fmt(v["barrier_ratio"], 1),
                _fmt(v["u_self_CS"], 3),
                _fmt(v["valley"]["depth"], 3),
            )
        )
    return (
        "\\begin{table}[!ht]\n\\centering\n"
        "\\caption{Execution noise. Every quantity is recomputed exactly for "
        "designs that invert each intended action with probability $\\eta$. "
        "$L^{\\dagger}$ is the guard threshold, $L^{*}_{\\CAS\\to\\AS}$ the "
        "liability protecting unconditional safety, and the window width their "
        "ratio; the barrier ratio is $L^{*}(0)/L^{*}(1)$ across the safe face. "
        "$u(\\CS,\\CS)$ is the residual harm of a conditionally safe population, "
        "which is zero only at $\\eta=0$. The valley depth is the largest "
        "increase of the basin-averaged unsafe frequency along the $L$-axis; it "
        "vanishes at $\\eta\\ge0.075$.}\n"
        "\\label{tab:noise}\n"
        "\\begin{tabular}{rrrrrrr}\n\\toprule\n"
        "$\\eta$ & $L^{\\dagger}$ & $L^{*}_{\\CAS\\to\\AS}$ & width & barrier ratio"
        " & $u(\\CS,\\CS)$ & valley depth \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_charges(ext: dict) -> str:
    rows = []
    for name in ("linear", "convex", "concave", "capped", "threshold"):
        d = ext["charges"][name]
        t = d["thresholds"]
        rows.append(
            "%s & %s & %s & %s & %s \\\\"
            % (
                CHANNEL_LABEL[name],
                _fmt(t["guard"], 2),
                _fmt(t["CAS_into_AS"], 2),
                _fmt(d["window_width"], 2) if d["window_width"] else "$\\infty$",
                _fmt(d["valley"]["depth"], 3),
            )
        )
    return (
        "\\begin{table}[!ht]\n\\centering\n"
        "\\caption{Non-linear liability. The charge is $L\\varphi(m)$ with "
        "$\\varphi$ increasing and normalised so that $\\varphi(9)=9$, which "
        "fixes the charge on a design that is unsafe throughout and makes $L$ "
        "comparable across shapes. Every threshold remains a ratio of a payoff "
        "difference to a charge difference. A de minimis rule that does not "
        "charge a single incident never protects unconditional safety, so its "
        "window is unbounded.}\n"
        "\\label{tab:charges}\n"
        "\\begin{tabular}{lrrrr}\n\\toprule\n"
        "charge shape & $L^{\\dagger}$ & $L^{*}_{\\CAS\\to\\AS}$ & width &"
        " valley depth \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_hysteresis(ext: dict) -> str:
    label = {
        "linear_theta0.9_eps0.05": ("$L(1-\\theta z)$, $\\theta=0.9$", "0.05"),
        "linear_theta0.9_eps0.01": ("$L(1-\\theta z)$, $\\theta=0.9$", "0.01"),
        "linear_theta0.9_eps0.20": ("$L(1-\\theta z)$, $\\theta=0.9$", "0.20"),
        "linear_theta0.5_eps0.05": ("$L(1-\\theta z)$, $\\theta=0.5$", "0.05"),
        "saturating_kappa9_eps0.05": ("$L/(1+\\kappa z)$, $\\kappa=9$", "0.05"),
        "saturating_kappa1_eps0.05": ("$L/(1+\\kappa z)$, $\\kappa=1$", "0.05"),
    }
    rows = []
    for key, (chan, eps) in label.items():
        d = ext["ratchet"][key]
        rows.append(
            "%s & %s & %s & %s & %s & %s & %s \\\\"
            % (
                chan,
                eps,
                _fmt(d["residual_fraction"], 2),
                _fmt(d["L_down_numeric"], 3),
                _fmt(d["L_up_numeric"], 3),
                _fmt(d["observed_ratio"], 2),
                _fmt(d["predicted_ratio"], 2),
            )
        )
    return (
        "\\begin{table}[!ht]\n\\centering\n"
        "\\caption{Hysteresis width across erosion channels and diffusion "
        "speeds. The quasi-static sweep starts in the protected regime with "
        "$z=0$; $L_{\\downarrow}$ and $L_{\\uparrow}$ are the last grid point at "
        "which protection holds on the descending branch and the first at which "
        "it is recovered on the ascending one, on a geometric grid whose "
        "spacing is a factor of $1.08$. The predicted loss threshold is "
        "$L^{*}_{\\CAS\\to\\CS}=0.551$ throughout. Changing $\\varepsilon$ by a "
        "factor of twenty leaves the loop unchanged, and the two channels agree "
        "wherever they share a residual fraction $\\rho$.}\n"
        "\\label{tab:hysteresis}\n"
        "\\begin{tabular}{llrrrrr}\n\\toprule\n"
        "channel & $\\varepsilon$ & $\\rho$ & $L_{\\downarrow}$ & $L_{\\uparrow}$"
        " & observed & $1/\\rho$ \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def figure_generality(ext: dict, outdir: Path) -> None:
    use_paper_style()
    fig, axes = new_figure(2.9, nrows=1, ncols=3)
    grid = np.array(ext["liability_grid"])

    # (A) execution noise
    ax = axes[0]
    etas = sorted(ext["noise"], key=float)
    x = [ext["noise"][k]["eta"] for k in etas]
    depth = [ext["noise"][k]["valley"]["depth"] for k in etas]
    width = [ext["noise"][k]["window_width"] for k in etas]
    ax.plot(x, depth, "-o", ms=3, color=PALETTE["unsafe"], label="valley depth")
    ax.set_xlabel(r"execution error rate $\eta$", fontsize=FS["label"])
    ax.set_ylabel("largest increase of $U$ with $L$", fontsize=FS["label"])
    ax.axhline(0.0, color=PALETTE["neutral"], lw=0.6, ls=":")
    twin = ax.twinx()
    twin.plot(x, width, "-s", ms=3, color=PALETTE["safe"], label="window width")
    twin.set_ylabel(r"window $L^{*}_{\mathrm{CAS}\to\mathrm{AS}}/L^{\dagger}$",
                    fontsize=FS["label"])
    twin.tick_params(labelsize=FS["tick"])
    handles = [
        ax.lines[0],
        twin.lines[0],
    ]
    ax.legend(handles, ["valley depth", "window width"], fontsize=FS["legend"],
              loc="upper right", frameon=False)
    panel_title(ax, "A", "execution noise")

    # (B) alternative dynamics
    ax = axes[1]
    for key in ("replicator", "logit_beta10", "logit_beta1", "best_response",
                "aspiration_high"):
        d = ext["dynamics"][key]
        ax.plot(d["liabilities"], d["curve"], "-o", ms=2.4,
                label=DYNAMICS_LABEL[key])
    ax.set_xscale("symlog", linthresh=1.0)
    ax.set_xlabel(r"effective liability $L$", fontsize=FS["label"])
    ax.set_ylabel("long-run unsafe frequency", fontsize=FS["label"])
    fitted_legend(ax, loc="upper right")
    panel_title(ax, "B", "selection dynamics")

    # (C) non-linear charges
    ax = axes[2]
    for name in ("linear", "convex", "concave", "capped", "threshold"):
        d = ext["charges"][name]
        ax.plot(d["liabilities"], d["curve"], "-o", ms=2.4, label=CHANNEL_LABEL[name])
    ax.set_xscale("symlog", linthresh=1.0)
    ax.set_xlabel(r"liability level $L$", fontsize=FS["label"])
    ax.set_ylabel("long-run unsafe frequency", fontsize=FS["label"])
    fitted_legend(ax, loc="upper right")
    panel_title(ax, "C", "charge shape")

    save(fig, outdir / "fig10_generality.pdf")
    print("wrote", outdir / "fig10_generality.pdf")
    _ = grid


def main() -> None:
    ext = json.loads((RESULTS / "extensions.json").read_text(encoding="utf-8"))
    tables = RESULTS / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    (tables / "tab_noise.tex").write_text(table_noise(ext), encoding="utf-8")
    (tables / "tab_charges.tex").write_text(table_charges(ext), encoding="utf-8")
    (tables / "tab_hysteresis.tex").write_text(table_hysteresis(ext), encoding="utf-8")
    print("wrote three tables to", tables)
    figures = RESULTS / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    figure_generality(ext, figures)


if __name__ == "__main__":
    main()
