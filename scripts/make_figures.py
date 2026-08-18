r"""Generate every manuscript figure.

Every figure is saved at the standard width ``dls.plotting.FIG_WIDTH`` with a
fixed (uncropped) bounding box and is included at ``\linewidth``, so all figures
are reduced by the same factor on the page and their text renders at the same
size.  Font sizes come from ``dls.plotting.FS`` and are never chosen per panel.

Usage
-----
    python scripts/make_figures.py [--outdir results/figures] [--quick]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from dls.dynamics import stationary_analysis
from dls.functionals import build_functionals, build_selection_matrix
from dls.plotting import (
    FIG_WIDTH,
    FS,
    PALETTE,
    new_figure,
    panel_title,
    save,
    use_paper_style,
)
from dls.race import STRATEGIES, RaceParams, build_race_tables
from dls.ratchet import RatchetParams, hysteresis_sweep
from dls.theory import (
    bistability_window_exact,
    critical_cs_fraction,
    evaluation_filter,
    face_equilibrium,
    invasion_threshold,
    longrun_unsafe_replicator,
    longrun_unsafe_sml,
    matched_longrun_unsafe,
    safe_face_barrier,
)

BASELINE_P_MAX = 0.6
POOL3 = ("AS", "CS", "CAS")


# --------------------------------------------------------------------------
# Figure 2: the three functionals and the selection wedge
# --------------------------------------------------------------------------


def figure_functionals(base, outdir: Path) -> None:
    fun = build_functionals(base, lam=0.5, harm=10.0)
    panels = [
        (base.payoff, r"task payoff $a(i,j)$", "viridis"),
        (base.unsafe_count, r"unsafe actions $m(i,j)$", "magma"),
        (build_selection_matrix(base, 5.0), r"selection functional $\pi_P$, $L=5$", "viridis"),
        (fun.wedge, r"wedge $\Delta=(1-\lambda)h\,m$", "cividis"),
    ]
    fig, axes = new_figure(5.4, nrows=2, ncols=2)
    for k, (ax, (mat, title, cmap), lab) in enumerate(zip(axes.ravel(), panels, "ABCD")):
        # rectangular cells: an equal aspect ratio would letterbox the panel and
        # open a gap between the two columns
        im = ax.imshow(mat, cmap=cmap, aspect="auto")
        ax.set_xticks(range(len(STRATEGIES)), STRATEGIES)
        ax.set_yticks(range(len(STRATEGIES)), STRATEGIES)
        if k % 2 == 0:
            ax.set_ylabel("focal design $i$")
        if k >= 2:
            ax.set_xlabel("opponent design $j$")
        panel_title(ax, lab, title)
        ax.grid(False)
        span = float(mat.max() - mat.min())
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat[i, j]
                rel = (v - mat.min()) / (span + 1e-12)
                ax.text(
                    j, i, f"{v:.1f}", ha="center", va="center", fontsize=FS["tiny"],
                    color="white" if rel < 0.55 else "black",
                )
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cbar.ax.tick_params(labelsize=FS["tick"])
    save(fig, outdir / "fig02_functionals")


# --------------------------------------------------------------------------
# Figure 3: replicator phase portraits on the three-design simplex
# --------------------------------------------------------------------------


def figure_simplex(base, outdir: Path) -> None:
    """Phase portraits drawn with the EGTtools simplex plotting utilities.

    The axes are positioned by hand, in inches.  The simplex is drawn with an
    equal aspect ratio, so a panel box that does not already have the aspect
    ratio of the view is letterboxed, and that is what opens the wide blank
    bands between the rows.  Sizing the boxes to the view removes them.
    """
    from egttools.plotting import plot_replicator_dynamics_in_simplex

    sub = base.subset(POOL3)
    liabilities = [0.05, 1.5, 10.0, 45.0]
    subtitles = [
        r"$L=0.05$: unsafe attractor",
        r"$L=1.5$: safe face protected",
        r"$L=10$: bistable",
        r"$L=45$: CAS eliminated",
    ]

    # view box (data units) and panel geometry (inches)
    xlim, ylim = (-0.235, 1.235), (-0.12, 1.03)
    view_aspect = (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])
    ml, mr, gx = 0.05, 0.05, 0.20          # left margin, right margin, column gap
    mt, gy, mb = 0.26, 0.30, 0.40          # title band, row gap, legend band
    aw = (FIG_WIDTH - ml - mr - gx) / 2.0
    ah = aw / view_aspect
    height = mt + 2 * ah + gy + mb

    fig = plt.figure(figsize=(FIG_WIDTH, height))
    corners = [
        (ml, mb + ah + gy), (ml + aw + gx, mb + ah + gy),   # row A B
        (ml, mb), (ml + aw + gx, mb),                       # row C D
    ]
    axes = [
        fig.add_axes([x / FIG_WIDTH, y / height, aw / FIG_WIDTH, ah / height])
        for x, y in corners
    ]

    for ax, L, subtitle, letter in zip(axes, liabilities, subtitles, "ABCD"):
        pi_p = np.ascontiguousarray(build_selection_matrix(sub, L))
        simplex, gradient_fn, roots, roots_xy, stability = (
            plot_replicator_dynamics_in_simplex(payoff_matrix=pi_p, ax=ax)
        )
        (
            simplex.add_axis(ax=ax)
            .draw_triangle()
            .draw_gradients(zorder=0, linewidth=0.7, density=1.1, arrowsize=0.9)
            .draw_stationary_points(roots_xy, stability, zorder=5)
            .add_vertex_labels(POOL3, epsilon_bottom=0.10, epsilon_top=0.09,
                               fontsize=FS["label"])
        )

        # the analytic interior rest point of the AS-CAS edge, for comparison
        eq = face_equilibrium(sub, "AS", "CAS", L)
        if eq.fraction_second is not None and eq.stable:
            bary = np.zeros(3)
            bary[POOL3.index("AS")] = 1.0 - eq.fraction_second
            bary[POOL3.index("CAS")] = eq.fraction_second
            pt = bary @ np.asarray(simplex.corners, dtype=float)
            ax.plot(pt[0], pt[1], "*", ms=9, color=PALETTE["accent"],
                    markeredgecolor="k", markeredgewidth=0.5, zorder=7)

        ax.axis("off")
        ax.set_aspect("equal")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        panel_title(ax, letter, subtitle, pad=5.0)

    handles = [
        Line2D([], [], color="#4C72B0", lw=1.0, label="replicator flow (colour: speed)"),
        Line2D([], [], marker="o", ls="", ms=5, color="k", label="rest point"),
        Line2D([], [], marker="*", ls="", ms=8, color=PALETTE["accent"],
               markeredgecolor="k", label="analytic interior rest point"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3,
               bbox_to_anchor=(0.5, 0.012), fontsize=FS["legend"])
    save(fig, outdir / "fig03_simplex")


# --------------------------------------------------------------------------
# Figure 4: bifurcation diagram in the effective liability
# --------------------------------------------------------------------------


def figure_bifurcation(base, outdir: Path, quick: bool = False) -> pd.DataFrame:
    sub = base.subset(POOL3)
    l_cas_cs = invasion_threshold(base, "CAS", "CS").critical_liability
    l_cs_cas = invasion_threshold(base, "CS", "CAS").critical_liability
    l_as_cas = invasion_threshold(base, "AS", "CAS").critical_liability
    l_cas_as = invasion_threshold(base, "CAS", "AS").critical_liability
    window = bistability_window_exact(base)
    assert window is not None
    l_guard, _ = window

    n = 90 if quick else 200
    grid = np.unique(np.concatenate([
        np.geomspace(1e-2, 60.0, n),
        np.array([l_cs_cas, l_cas_cs, l_as_cas, l_guard, l_cas_as]) * (1 + 1e-9),
    ]))

    rep = np.array([
        longrun_unsafe_replicator(base, L, pool=POOL3, n_starts=40 if quick else 110)
        for L in grid
    ])
    sml = np.array([longrun_unsafe_sml(base, L, pool=POOL3, population_size=50) for L in grid])

    fine = np.geomspace(1e-2, 60.0, 3000)
    branch_cascas = np.full_like(fine, np.nan)
    branch_ascas = np.full_like(fine, np.nan)
    for k, L in enumerate(fine):
        e1 = face_equilibrium(sub, "CS", "CAS", L)
        if e1.stable:
            branch_cascas[k] = e1.unsafe_frequency
        e2 = face_equilibrium(sub, "AS", "CAS", L)
        if e2.stable:
            branch_ascas[k] = e2.unsafe_frequency

    fig, ax = new_figure(3.9)
    ax.axvspan(l_guard, l_cas_as, color=PALETTE["accent"], alpha=0.13, lw=0,
               label="bistability window")

    ax.plot(fine[fine <= l_cs_cas], np.ones((fine <= l_cs_cas).sum()),
            color=PALETTE["CAS"], lw=2.2, label="CAS attractor")
    ax.plot(fine, branch_cascas, color=PALETTE["CAS"], lw=2.2, ls=(0, (4, 2)),
            label="CS-CAS coexistence")
    mask_inv = fine < l_guard
    ax.plot(np.where(mask_inv, fine, np.nan), np.where(mask_inv, branch_ascas, np.nan),
            color=PALETTE["AU"], lw=1.4, ls=":", label="AS-CAS, CS-invadable")
    ax.plot(np.where(~mask_inv, fine, np.nan), np.where(~mask_inv, branch_ascas, np.nan),
            color=PALETTE["AU"], lw=2.2, label="AS-CAS, uninvadable")
    ax.plot(fine[fine >= l_cas_cs], np.zeros((fine >= l_cas_cs).sum()),
            color=PALETTE["CS"], lw=2.2, label="protected safe face")

    ax.plot(grid, rep, "o", ms=3.0, color=PALETTE["neutral"], alpha=0.85,
            label="replicator basin average")
    ax.plot(grid, sml, "-", lw=1.2, color=PALETTE["safe"],
            label=r"finite $Z=50$, small mutation")

    for L, txt, dy in [
        (l_cs_cas, r"$L^{*}_{\mathrm{CS}\to\mathrm{CAS}}$", 1.16),
        (l_cas_cs, r"$L^{*}_{\mathrm{CAS}\to\mathrm{CS}}$", 1.06),
        (l_as_cas, r"$L^{*}_{\mathrm{AS}\to\mathrm{CAS}}$", 1.16),
        (l_guard, r"$L^{\dagger}$", 1.06),
        (l_cas_as, r"$L^{*}_{\mathrm{CAS}\to\mathrm{AS}}$", 1.16),
    ]:
        ax.axvline(L, color=PALETTE["neutral"], lw=0.6, ls="--", alpha=0.55)
        ax.text(L, dy, txt, ha="center", va="bottom", fontsize=FS["tiny"])

    ax.set_xscale("log")
    ax.set_xlabel(r"effective liability $L=\lambda h$  (payoff units per Unsafe action)")
    ax.set_ylabel(r"long-run Unsafe frequency $U^{*}$")
    ax.set_ylim(-0.04, 1.26)
    ax.set_xlim(1e-2, 60)
    fig.legend(loc="outside lower center", ncol=3, fontsize=FS["legend"],
               columnspacing=1.0, handlelength=1.8, handletextpad=0.5)
    save(fig, outdir / "fig04_bifurcation")

    return pd.DataFrame(
        {"effective_liability": grid, "unsafe_replicator": rep, "unsafe_sml": sml}
    )


# --------------------------------------------------------------------------
# Figure 5: futility of solo evaluation filters
# --------------------------------------------------------------------------


def figure_filter(base, outdir: Path, quick: bool = False) -> pd.DataFrame:
    pools = {
        r"no filter  $\{$AS, AU, CS, CAS$\}$": evaluation_filter(base, 1.0),
        r"$\varepsilon=0.2$  $\{$AS, CS, CAS$\}$": evaluation_filter(base, 0.2),
        r"$\varepsilon=0.05$  $\{$AS, CS$\}$": evaluation_filter(base, 0.05),
    }
    styles = [
        (PALETTE["neutral"], "-", 2.4),
        (PALETTE["CAS"], "--", 1.9),
        (PALETTE["CS"], ":", 2.4),
    ]
    grid = np.geomspace(1e-2, 60.0, 60 if quick else 120)

    rows = []
    fig, axes = new_figure(2.9, nrows=1, ncols=2, width_ratios=[1.3, 1])
    ax = axes[0]
    for (label, pool), (c, ls, lw) in zip(pools.items(), styles):
        # a matched start measure: initial conditions are always drawn on the
        # {AS, CS, CAS} simplex, so pools of different size are compared from
        # the same ecosystem rather than from different sampling measures
        vals = [
            matched_longrun_unsafe(base, L, pool=pool, n_starts=40 if quick else 100)
            for L in grid
        ]
        ax.plot(grid, vals, color=c, ls=ls, lw=lw, label=label)
        rows += [
            {"pool": "+".join(pool), "effective_liability": L, "unsafe": v}
            for L, v in zip(grid, vals)
        ]
    ax.set_xscale("log")
    ax.set_xlabel(r"effective liability $L$")
    ax.set_ylabel(r"long-run Unsafe frequency $U^{*}$")
    ax.set_ylim(-0.04, 1.06)
    ax.legend(loc="upper right", fontsize=FS["legend"], handlelength=1.8)
    panel_title(ax, "A", "solo evaluation removes designs")

    ax = axes[1]
    scores = [base.unsafe_frequency[k, base.strategies.index("AS")] for k in range(4)]
    equilibrium = [base.unsafe_frequency[base.strategies.index(s),
                                         base.strategies.index(s)] for s in STRATEGIES]
    xpos = np.arange(4)
    b1 = ax.bar(xpos - 0.2, scores, width=0.38, color=PALETTE["safe"],
                label=r"solo: $u(i,\mathrm{AS})$")
    b2 = ax.bar(xpos + 0.2, equilibrium, width=0.38, color=PALETTE["unsafe"],
                label=r"self-play: $u(i,i)$")
    for rect, v in list(zip(b1, scores)) + list(zip(b2, equilibrium)):
        ax.annotate(f"{v:.2f}", (rect.get_x() + rect.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 2), ha="center",
                    fontsize=FS["tiny"], color=PALETTE["neutral"])
    ax.axhline(0.2, color=PALETTE["neutral"], ls="--", lw=0.8)
    ax.text(-0.55, 0.225, r"$\varepsilon=0.2$", fontsize=FS["annot"], ha="left",
            color=PALETTE["neutral"])
    ax.set_xticks(xpos, STRATEGIES)
    ax.set_ylabel("Unsafe frequency")
    ax.set_ylim(0, 1.38)
    ax.legend(loc="upper center", ncol=2, fontsize=FS["legend"], columnspacing=1.0,
              handlelength=1.4)
    panel_title(ax, "B", "what the evaluation sees")

    save(fig, outdir / "fig05_filter")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Figure 6: the safe face, its barrier and neutral drift
# --------------------------------------------------------------------------


def figure_safe_face(base, outdir: Path) -> pd.DataFrame:
    xs = np.linspace(0.0, 1.0, 400)
    barrier = np.array([safe_face_barrier(base, x) for x in xs])

    fig, axes = new_figure(2.55, nrows=1, ncols=3)

    ax = axes[0]
    ax.plot(xs, barrier, color=PALETTE["CS"], lw=2.2)
    ax.set_yscale("log")
    ax.set_xlabel(r"share of CS on the face, $x$")
    ax.set_ylabel(r"invasion barrier $L^{*}(x)$")
    panel_title(ax, "A", "barrier of a mixed face")
    ax.annotate(f"{barrier[0]:.1f}", (0.0, barrier[0]), textcoords="offset points",
                xytext=(10, 1), fontsize=FS["annot"])
    ax.annotate(f"{barrier[-1]:.2f}", (1.0, barrier[-1]), textcoords="offset points",
                xytext=(-26, 4), fontsize=FS["annot"])

    ax = axes[1]
    ls = np.geomspace(0.3, 60.0, 400)
    crit = np.array([critical_cs_fraction(base, L) for L in ls])
    ax.plot(ls, crit, color=PALETTE["accent"], lw=2.2)
    ax.fill_between(ls, crit, 1.0, color=PALETTE["safe"], alpha=0.14)
    ax.fill_between(ls, 0.0, crit, color=PALETTE["unsafe"], alpha=0.14)
    ax.text(1.15, 0.26, "vulnerable", fontsize=FS["annot"], color=PALETTE["unsafe"])
    ax.text(9.0, 0.74, "protected", fontsize=FS["annot"], color=PALETTE["safe"])
    ax.set_xscale("log")
    ax.set_xlabel(r"effective liability $L$")
    ax.set_ylabel(r"critical share $x^{*}(L)$")
    panel_title(ax, "B", "CS needed at each $L$")

    # neutral drift on the AS-CS edge
    ax = axes[2]
    edge = base.subset(("AS", "CS"))
    pi_p = build_selection_matrix(edge, 5.0)
    rows = []
    Z = 100
    for mu, c in zip((0.002, 0.02, 0.2), (PALETTE["AS"], PALETTE["neutral"], PALETTE["CS"])):
        res = stationary_analysis(pi_p, edge.unsafe_frequency, population_size=Z,
                                  beta=0.05, mu=mu)
        dist = res.state_distribution
        frac = np.arange(len(dist)) / (len(dist) - 1)
        ax.plot(frac, dist / dist.max(), color=c, lw=1.7, label=rf"$\mu={mu}$")
        xstar = critical_cs_fraction(base, 5.0)
        rows.append({"mu": mu, "Z": Z, "L": 5.0,
                     "prob_vulnerable": float(dist[frac < xstar].sum())})
    xstar = critical_cs_fraction(base, 5.0)
    # stop the marker and the shading below the legend band
    top = 1.05 / 1.62
    ax.axvline(xstar, ymax=top, color=PALETTE["unsafe"], ls="--", lw=1.1)
    ax.text(xstar + 0.03, 0.30, r"$x^{*}(L{=}5)$", fontsize=FS["annot"], ha="left",
            va="center", color=PALETTE["unsafe"])
    ax.axvspan(0, xstar, ymax=top, color=PALETTE["unsafe"], alpha=0.10, lw=0)
    ax.set_xlabel(r"share of CS on the face")
    ax.set_ylabel("stationary density (scaled)")
    # headroom for the legend: the blue curve spikes to 1 at both ends
    ax.set_ylim(0, 1.62)
    panel_title(ax, "C", "neutral drift")
    ax.legend(fontsize=FS["legend"], loc="upper center", ncol=3, columnspacing=0.8,
              handlelength=1.2, borderpad=0.2)

    save(fig, outdir / "fig06_safe_face")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Figure 7: finite-population stationary behaviour
# --------------------------------------------------------------------------


def figure_finite(base, outdir: Path, quick: bool = False) -> pd.DataFrame:
    sub = base.subset(POOL3)
    n_l = 40 if quick else 90
    ls = np.geomspace(1e-2, 60.0, n_l)
    betas = np.geomspace(2e-3, 1.0, 18 if quick else 34)
    zs = np.array([10, 20, 30, 50, 75, 100, 150, 200])

    heat = np.zeros((len(betas), len(ls)))
    for a, b in enumerate(betas):
        for c, L in enumerate(ls):
            heat[a, c] = longrun_unsafe_sml(sub, L, population_size=50, beta=float(b))

    heat_z = np.zeros((len(zs), len(ls)))
    for a, Z in enumerate(zs):
        for c, L in enumerate(ls):
            heat_z[a, c] = longrun_unsafe_sml(sub, L, population_size=int(Z), beta=0.05)

    fig, axes = new_figure(2.7, nrows=1, ncols=2)
    for ax, data, yvals, ylabel, show_cbar_label in [
        (axes[0], heat, betas, r"selection intensity $\beta$", False),
        (axes[1], heat_z, zs, r"population size $Z$", True),
    ]:
        mesh = ax.pcolormesh(ls, yvals, data, cmap="RdYlBu_r", vmin=0, vmax=1,
                             shading="nearest")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"effective liability $L$")
        ax.set_ylabel(ylabel)
        ax.grid(False)
        for L in (invasion_threshold(base, "CAS", "CS").critical_liability,
                  invasion_threshold(base, "CAS", "AS").critical_liability):
            ax.axvline(L, color="k", lw=0.7, ls="--", alpha=0.6)
        cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
        cbar.ax.tick_params(labelsize=FS["tick"])
        if show_cbar_label:
            cbar.set_label(r"stationary $U^{*}$", fontsize=FS["label"])
    panel_title(axes[0], "A", r"$Z=50$, varying $\beta$")
    panel_title(axes[1], "B", r"$\beta=0.05$, varying $Z$")
    save(fig, outdir / "fig07_finite")

    rows = [
        {"beta": float(b), "effective_liability": float(L), "unsafe": float(heat[a, c])}
        for a, b in enumerate(betas)
        for c, L in enumerate(ls)
    ]
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Figure 8: eco-evolutionary ratchet and hysteresis
# --------------------------------------------------------------------------


def figure_hysteresis(base, outdir: Path, quick: bool = False) -> pd.DataFrame:
    sub = base.subset(POOL3)
    params = RatchetParams(theta=0.9, epsilon=0.05, mutation=1e-6)
    grid = np.geomspace(0.12, 25.0, 40 if quick else 90)
    # the decreasing branch starts inside the protected regime, so that the
    # ratchet variable is switched on only by the transition itself
    protected = np.array([0.02, 0.96, 0.02])
    sweep = hysteresis_sweep(sub, params, grid, x0=protected, t_end=3000.0)

    l_down = invasion_threshold(base, "CAS", "CS").critical_liability
    l_up = l_down / (1.0 - params.theta)

    fig, axes = new_figure(3.1, nrows=1, ncols=2)

    ax = axes[0]
    ax.plot(sweep.liability_values, sweep.unsafe_forward, "-o", ms=2.6,
            color=PALETTE["safe"], label=r"$L$ decreasing, $z=0$ initially")
    ax.plot(sweep.liability_values, sweep.unsafe_backward, "-s", ms=2.6,
            color=PALETTE["unsafe"], label=r"$L$ increasing, capability diffused")
    ax.axvline(l_down, color=PALETTE["neutral"], ls="--", lw=0.7)
    ax.axvline(l_up, color=PALETTE["neutral"], ls="--", lw=0.7)
    ax.annotate("", xy=(l_up, 0.52), xytext=(l_down, 0.52),
                arrowprops=dict(arrowstyle="<->", lw=0.8, color=PALETTE["accent"]))
    ax.text(np.sqrt(l_down * l_up), 0.55,
            rf"$\times {l_up / l_down:.0f}$", ha="center", fontsize=FS["annot"],
            color=PALETTE["accent"])
    ax.set_xscale("log")
    ax.set_xlabel(r"base effective liability $L$")
    ax.set_ylabel(r"long-run Unsafe frequency $U^{*}$")
    ax.set_ylim(-0.05, 1.08)
    panel_title(ax, "A", f"hysteresis loop, area $=$ {sweep.loop_area:.2f}")

    ax = axes[1]
    ax.plot(sweep.liability_values, sweep.z_forward, "-o", ms=2.6,
            color=PALETTE["safe"])
    ax.plot(sweep.liability_values, sweep.z_backward, "-s", ms=2.6,
            color=PALETTE["unsafe"])
    ax.set_xscale("log")
    ax.set_xlabel(r"base effective liability $L$")
    ax.set_ylabel(r"diffused capability stock $z$")
    ax.set_ylim(-0.05, 1.08)
    panel_title(ax, "B", "the ratchet never decreases")

    # both panels show the same two sweeps, so a single figure-level legend serves
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2,
               fontsize=FS["legend"])

    save(fig, outdir / "fig08_hysteresis")
    return pd.DataFrame(
        {
            "effective_liability": sweep.liability_values,
            "unsafe_decreasing": sweep.unsafe_forward,
            "unsafe_increasing": sweep.unsafe_backward,
            "z_decreasing": sweep.z_forward,
            "z_increasing": sweep.z_backward,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("results/figures"))
    parser.add_argument("--tabledir", type=Path, default=Path("results/tables"))
    parser.add_argument("--quick", action="store_true")
    parser.add_argument(
        "--only", nargs="*", default=None,
        help="subset of figure numbers to build, e.g. --only 5 6 7",
    )
    args = parser.parse_args()

    use_paper_style()
    args.outdir.mkdir(parents=True, exist_ok=True)
    args.tabledir.mkdir(parents=True, exist_ok=True)

    base = build_race_tables(RaceParams(p_max=BASELINE_P_MAX))

    jobs = {
        "2": ("functionals", lambda: figure_functionals(base, args.outdir)),
        "3": ("simplex", lambda: figure_simplex(base, args.outdir)),
        "4": ("bifurcation", lambda: figure_bifurcation(base, args.outdir, args.quick)
              .to_csv(args.tabledir / "bifurcation.csv", index=False)),
        "5": ("filter futility", lambda: figure_filter(base, args.outdir, args.quick)
              .to_csv(args.tabledir / "filter_curves.csv", index=False)),
        "6": ("safe face", lambda: figure_safe_face(base, args.outdir)
              .to_csv(args.tabledir / "neutral_drift.csv", index=False)),
        "7": ("finite population", lambda: figure_finite(base, args.outdir, args.quick)
              .to_csv(args.tabledir / "finite_heatmap.csv", index=False)),
        "8": ("hysteresis", lambda: figure_hysteresis(base, args.outdir, args.quick)
              .to_csv(args.tabledir / "hysteresis.csv", index=False)),
    }
    selected = args.only if args.only else list(jobs)
    for key in selected:
        name, fn = jobs[key]
        print(f"fig0{key} {name} ...", flush=True)
        fn()
    print("done ->", args.outdir)


if __name__ == "__main__":
    main()
