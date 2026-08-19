"""Turn ``results/round4.json`` into the manuscript's tables and figure.

Writes ``results/tables/tab_attribution.tex``, ``tab_assortment.tex`` and
``results/figures/fig11_observation.pdf``.

    python scripts/emit_round4.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dls.plotting import (
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

Q_SHOWN = ("0.00", "0.10", "0.25", "0.50")
R_SHOWN = ("0.000", "0.050", "0.100", "0.200", "0.300", "0.400")


def _fmt(value, digits=3, inf="$\\infty$"):
    if value is None:
        return "--"
    if not np.isfinite(value):
        return inf
    return ("%%.%df" % digits) % value


def table_attribution(data: dict) -> str:
    rows = []
    for key in Q_SHOWN:
        v = data["attribution"]["curves"][key]
        rows.append(
            "%.2f & %s & %s & %s & %s & %s \\\\"
            % (
                v["q"],
                _fmt(v["guard"], 2),
                _fmt(v["CAS_into_AS"], 2),
                _fmt(v["window"], 2),
                _fmt(v["barrier_AS"] / v["barrier_CS"], 1),
                _fmt(v["valley"]["depth"], 3),
            )
        )
    return (
        "\\begin{table}[!ht]\n\\centering\n"
        "\\caption{Misattribution. A fixed quantity of blame is split between "
        "the two parties to an interaction and a fraction $q$ of it lands on "
        "the wrong one, so the charge base is "
        "$(1-q)\\,m(i,j)+q\\,m(j,i)$. The guard threshold barely moves, because "
        "both designs it compares are active against the same aggressor. The "
        "liability protecting unconditional safety diverges as $1/(1-q)$, "
        "because the design a first strike exploits has by construction a "
        "spotless record, so blame moved onto it is blame destroyed. The window "
        "widens and the valley deepens accordingly.}\n"
        "\\label{tab:attribution}\n"
        "\\begin{tabular}{rrrrrr}\n\\toprule\n"
        "$q$ & $L^{\\dagger}$ & $L^{*}_{\\CAS\\to\\AS}$ & width & barrier ratio"
        " & valley depth \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_assortment(data: dict) -> str:
    rows = []
    for key in R_SHOWN:
        v = data["assortment"]["curves"][key]
        window = v["window"]
        rows.append(
            "%.2f & %s & %s & %s & %s & %s \\\\"
            % (
                v["r"],
                _fmt(v["guard"], 3),
                _fmt(v["CAS_into_AS"], 2),
                _fmt(v["barrier_CS"], 3),
                "closed" if window == 0.0 else _fmt(window, 2),
                _fmt(v["valley"]["depth"], 3),
            )
        )
    closing = data["assortment"]["closing_r"]
    free = data["assortment"]["free_protection_CS_r"]
    return (
        "\\begin{table}[!ht]\n\\centering\n"
        "\\caption{Assortative matching. A design meets a copy of itself with "
        "probability $r$ and a random partner otherwise, which is the "
        "replicator dynamics of the transformed matrix "
        "$\\tilde\\pi(i,j)=r\\,\\piP(i,i)+(1-r)\\,\\piP(i,j)$. The guard "
        "threshold does not move at all: the assortment correction is a "
        "self-interaction term, and the two designs it compares are "
        "self-identical. The upper edge falls, so the window narrows from "
        "above and closes at $r=%.3f$; a negative $L^{*}_{\\CAS\\to\\CS}$ means "
        "conditional safety is protected with no liability at all, which "
        "happens from $r=%.3f$.}\n"
        "\\label{tab:assortment}\n"
        "\\begin{tabular}{rrrrrr}\n\\toprule\n"
        "$r$ & $L^{\\dagger}$ & $L^{*}_{\\CAS\\to\\AS}$ & $L^{*}_{\\CAS\\to\\CS}$"
        " & width & valley depth \\\\\n\\midrule\n"
        % (closing, free)
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def _harm_panel(ax, grid, curves, keys, colours, symbol, values):
    for colour, key, value in zip(colours, keys, values):
        ax.plot(grid, curves[key]["curve"], "-o", ms=2.2, color=colour,
                label=r"$%s=%.2f$" % (symbol, value))
    ax.set_xscale("symlog", linthresh=1.0)
    ax.set_xlabel(r"effective liability $L$", fontsize=FS["label"])
    ax.set_ylabel("long-run unsafe frequency", fontsize=FS["label"])


def _edge_panel(ax, xs, guard, upper, xlabel, closing=None):
    """Both edges of the bistable window, with the window itself shaded."""
    inside = upper > guard
    ax.fill_between(xs[inside], guard[inside], upper[inside],
                    color=PALETTE["unsafe"], alpha=0.16, lw=0,
                    label="bistable window")
    ax.plot(xs, guard, "-", color=PALETTE["CS"], label=r"$L^{\dagger}$")
    ax.plot(xs, upper, "-", color=PALETTE["unsafe"],
            label=r"$L^{*}_{\mathrm{CAS}\to\mathrm{AS}}$")
    if closing is not None:
        ax.axvline(closing, color=PALETTE["neutral"], lw=0.8, ls="--")
    ax.set_xlabel(xlabel, fontsize=FS["label"])
    ax.set_ylabel(r"effective liability $L$", fontsize=FS["label"])


def figure_observation(data: dict, outdir: Path) -> None:
    use_paper_style()
    fig, axes = new_figure(5.4, nrows=2, ncols=2)

    # (A) misattribution: long-run harm
    ax = axes[0, 0]
    shades = [PALETTE["safe"], PALETTE["CS"], PALETTE["accent"], PALETTE["unsafe"]]
    _harm_panel(
        ax,
        np.array(data["attribution"]["grid"]),
        data["attribution"]["curves"],
        Q_SHOWN,
        shades,
        "q",
        [data["attribution"]["curves"][k]["q"] for k in Q_SHOWN],
    )
    fitted_legend(ax, loc="upper right", ncol=2)
    panel_title(ax, "A", "misattributed blame")

    # (B) misattribution: the two edges
    ax = axes[0, 1]
    sweep = data["attribution"]["sweep"]
    qs = np.array([s["q"] for s in sweep])
    _edge_panel(
        ax,
        qs,
        np.array([s["guard"] for s in sweep]),
        np.array([s["CAS_into_AS"] for s in sweep]),
        r"blame booked against the wrong party, $q$",
    )
    ax.set_yscale("log")
    ax.set_ylim(1.0, 1200.0)
    ax.annotate(r"$L^{*}\propto 1/(1-q)$", xy=(0.44, 13.0),
                fontsize=FS["annot"], color=PALETTE["unsafe"], ha="left")
    fitted_legend(ax, loc="upper left")
    panel_title(ax, "B", "the window widens without bound")

    # (C) assortment: long-run harm
    ax = axes[1, 0]
    cmap = [PALETTE["unsafe"], PALETTE["accent"], PALETTE["CAS"],
            PALETTE["CS"], PALETTE["safe"], PALETTE["neutral"]]
    _harm_panel(
        ax,
        np.array(data["assortment"]["grid"]),
        data["assortment"]["curves"],
        R_SHOWN,
        cmap,
        "r",
        [data["assortment"]["curves"][k]["r"] for k in R_SHOWN],
    )
    fitted_legend(ax, loc="upper right", ncol=2)
    panel_title(ax, "C", "assortative matching")

    # (D) assortment: the two edges
    ax = axes[1, 1]
    sweep = data["assortment"]["sweep"]
    rs = np.array([s["r"] for s in sweep])
    closing = data["assortment"]["closing_r"]
    _edge_panel(
        ax,
        rs,
        np.array([s["guard"] for s in sweep]),
        np.array([max(s["CAS_into_AS"], 0.0) for s in sweep]),
        r"assortment $r$",
        closing=closing,
    )
    ax.set_ylim(0.0, 46.0)
    ax.annotate(r"closes at $r=%.3f$" % closing, xy=(closing + 0.015, 24.0),
                fontsize=FS["annot"], color=PALETTE["neutral"], ha="left")
    fitted_legend(ax, loc="upper right")
    panel_title(ax, "D", "the window closes from above")

    save(fig, outdir / "fig11_observation.pdf")
    print("wrote", outdir / "fig11_observation.pdf")


def main() -> None:
    data = json.loads((RESULTS / "round4.json").read_text(encoding="utf-8"))
    tables = RESULTS / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    (tables / "tab_attribution.tex").write_text(table_attribution(data), encoding="utf-8")
    (tables / "tab_assortment.tex").write_text(table_assortment(data), encoding="utf-8")
    print("wrote two tables to", tables)
    figures = RESULTS / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    figure_observation(data, figures)


if __name__ == "__main__":
    main()
