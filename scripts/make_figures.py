"""Generate every manuscript figure.

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
from dls.plotting import PALETTE, panel_label, save, use_paper_style
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
    fig, axes = plt.subplots(1, 4, figsize=(11.6, 3.0))
    fig.subplots_adjust(wspace=0.55)
    for k, (ax, (mat, title, cmap), lab) in enumerate(zip(axes, panels, "ABCD")):
        im = ax.imshow(mat, cmap=cmap, aspect="equal")
        ax.set_xticks(range(len(STRATEGIES)), STRATEGIES, fontsize=7.2)
        if k == 0:
            ax.set_yticks(range(len(STRATEGIES)), STRATEGIES, fontsize=7.2)
            ax.set_ylabel("focal design $i$", fontsize=8.4)
        else:
            ax.set_yticks(range(len(STRATEGIES)), [""] * len(STRATEGIES))
        ax.set_xlabel("opponent design $j$", fontsize=8.4)
        ax.set_title(title, fontsize=8.4, pad=6)
        ax.grid(False)
        span = float(mat.max() - mat.min())
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                v = mat[i, j]
                rel = (v - mat.min()) / (span + 1e-12)
                ax.text(
                    j, i, f"{v:.1f}", ha="center", va="center", fontsize=6.4,
                    color="white" if rel < 0.55 else "black",
                )
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(labelsize=6.2)
        panel_label(ax, lab, dx=-0.28 if k == 0 else -0.16, dy=1.22)
    save(fig, outdir / "fig02_functionals")


# --------------------------------------------------------------------------
# Figure 3: replicator phase portraits on the three-design simplex
# --------------------------------------------------------------------------


def _simplex_coords(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Barycentric to Cartesian for a 3-simplex drawn as an equilateral triangle."""
    v = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, np.sqrt(3) / 2]])
    pts = x @ v
    return pts[..., 0], pts[..., 1]


def figure_simplex(base, outdir: Path, n_traj: int = 26) -> None:
    from dls.dynamics import integrate_replicator

    sub = base.subset(POOL3)
    liabilities = [0.05, 1.5, 10.0, 45.0]
    titles = [
        "A   " + r"$L=0.05$: unsafe attractor",
        "B   " + r"$L=1.5$: safe face protected",
        "C   " + r"$L=10$: bistable",
        "D   " + r"$L=45$: CAS eliminated",
    ]
    rng = np.random.default_rng(7)

    fig, axes = plt.subplots(1, 4, figsize=(11.2, 3.2))
    verts = np.eye(3)
    vx, vy = _simplex_coords(verts)

    for ax, L, title, lab in zip(axes, liabilities, titles, "ABCD"):
        pi_p = build_selection_matrix(sub, L)
        ax.plot(
            np.append(vx, vx[0]), np.append(vy, vy[0]),
            color=PALETTE["neutral"], lw=1.0, zorder=3,
        )
        # streamlines from random interior starts
        for _ in range(n_traj):
            x0 = rng.dirichlet(np.ones(3) * 0.7)
            _, traj = integrate_replicator(pi_p, x0, t_end=900.0, n_points=600)
            tx, ty = _simplex_coords(traj)
            ax.plot(tx, ty, color="#7F7F7F", lw=0.55, alpha=0.75, zorder=2)
            ax.plot(tx[-1], ty[-1], "o", ms=3.0, color=PALETTE["unsafe"], zorder=4)
            ax.plot(tx[0], ty[0], ".", ms=2.0, color="#BBBBBB", zorder=1)

        # analytic interior rest point of the AS-CAS edge
        eq = face_equilibrium(sub, "AS", "CAS", L)
        if eq.fraction_second is not None and eq.stable:
            xstar = np.zeros(3)
            xstar[POOL3.index("AS")] = 1 - eq.fraction_second
            xstar[POOL3.index("CAS")] = eq.fraction_second
            ex, ey = _simplex_coords(xstar)
            ax.plot(ex, ey, "*", ms=9, color=PALETTE["accent"],
                    markeredgecolor="k", markeredgewidth=0.4, zorder=6)

        for k, s in enumerate(POOL3):
            dx = -0.06 if vx[k] < 0.4 else (0.06 if vx[k] > 0.6 else 0.0)
            dy = -0.075 if vy[k] < 0.1 else 0.045
            ax.text(vx[k] + dx, vy[k] + dy, s, ha="center", va="center",
                    fontsize=9, fontweight="bold", color=PALETTE[s])
        ax.set_title(title, fontsize=8.6, loc="left")
        ax.set_xlim(-0.14, 1.14)
        ax.set_ylim(-0.14, 1.02)
        ax.set_aspect("equal")
        ax.axis("off")

    handles = [
        Line2D([], [], color="#7F7F7F", lw=0.8, label="replicator trajectory"),
        Line2D([], [], marker="o", ls="", ms=4, color=PALETTE["unsafe"], label="end state"),
        Line2D([], [], marker="*", ls="", ms=8, color=PALETTE["accent"],
               markeredgecolor="k", label="analytic interior rest point"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06))
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

    n = 90 if quick else 260
    grid = np.unique(np.concatenate([
        np.geomspace(1e-2, 60.0, n),
        np.array([l_cs_cas, l_cas_cs, l_as_cas, l_guard, l_cas_as]) * (1 + 1e-9),
    ]))

    rep = np.array([
        longrun_unsafe_replicator(base, L, pool=POOL3, n_starts=40 if quick else 150)
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

    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    ax.axvspan(l_guard, l_cas_as, color=PALETTE["accent"], alpha=0.13, lw=0,
               label="bistability window")

    ax.plot(fine[fine <= l_cs_cas], np.ones((fine <= l_cs_cas).sum()),
            color=PALETTE["CAS"], lw=2.2, label="CAS attractor (analytic)")
    ax.plot(fine, branch_cascas, color=PALETTE["CAS"], lw=2.2, ls=(0, (4, 2)),
            label="CS-CAS coexistence (analytic)")
    mask_inv = fine < l_guard
    ax.plot(np.where(mask_inv, fine, np.nan), np.where(mask_inv, branch_ascas, np.nan),
            color=PALETTE["AU"], lw=1.4, ls=":", label="AS-CAS coexistence, CS-invadable")
    ax.plot(np.where(~mask_inv, fine, np.nan), np.where(~mask_inv, branch_ascas, np.nan),
            color=PALETTE["AU"], lw=2.2, label="AS-CAS coexistence, uninvadable")
    ax.plot(fine[fine >= l_cas_cs], np.zeros((fine >= l_cas_cs).sum()),
            color=PALETTE["CS"], lw=2.2, label="protected safe face (analytic)")

    ax.plot(grid, rep, "o", ms=3.0, color=PALETTE["neutral"], alpha=0.85,
            label="replicator, basin average")
    ax.plot(grid, sml, "-", lw=1.2, color=PALETTE["safe"],
            label=r"finite population, $Z=50$, small mutation")

    for L, txt in [
        (l_cs_cas, r"$L^{*}_{\mathrm{CS}\to\mathrm{CAS}}$"),
        (l_cas_cs, r"$L^{*}_{\mathrm{CAS}\to\mathrm{CS}}$"),
        (l_as_cas, r"$L^{*}_{\mathrm{AS}\to\mathrm{CAS}}$"),
        (l_guard, r"$L^{\dagger}$"),
        (l_cas_as, r"$L^{*}_{\mathrm{CAS}\to\mathrm{AS}}$"),
    ]:
        ax.axvline(L, color=PALETTE["neutral"], lw=0.6, ls="--", alpha=0.55)
        ax.text(L, 1.045, txt, rotation=0, ha="center", va="bottom", fontsize=6.4)

    ax.set_xscale("log")
    ax.set_xlabel(r"effective liability $L=\lambda h$  (payoff units per Unsafe action)")
    ax.set_ylabel(r"long-run Unsafe frequency $U^{*}$")
    ax.set_ylim(-0.04, 1.10)
    ax.set_xlim(1e-2, 60)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=7.0)
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
    grid = np.geomspace(1e-2, 60.0, 60 if quick else 160)

    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), width_ratios=[1.35, 1])
    ax = axes[0]
    for (label, pool), (c, ls, lw) in zip(pools.items(), styles):
        # a matched start measure: initial conditions are always drawn on the
        # {AS, CS, CAS} simplex, so pools of different size are compared from
        # the same ecosystem rather than from different sampling measures
        vals = [
            matched_longrun_unsafe(base, L, pool=pool, n_starts=40 if quick else 150)
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
    ax.legend(loc="upper right", fontsize=7.2)
    ax.set_title("removing designs that fail a solo evaluation", fontsize=8.6)
    panel_label(ax, "A")

    ax = axes[1]
    scores = [base.unsafe_frequency[k, base.strategies.index("AS")] for k in range(4)]
    equilibrium = []
    for s in STRATEGIES:
        idx = base.strategies.index(s)
        equilibrium.append(base.unsafe_frequency[idx, idx])
    xpos = np.arange(4)
    ax.bar(xpos - 0.2, scores, width=0.38, color=PALETTE["safe"],
           label="solo evaluation: $u(i,\\mathrm{AS})$")
    ax.bar(xpos + 0.2, equilibrium, width=0.38, color=PALETTE["unsafe"],
           label="self-play: $u(i,i)$")
    ax.axhline(0.2, color=PALETTE["neutral"], ls="--", lw=0.8)
    ax.text(3.42, 0.225, r"$\varepsilon=0.2$", fontsize=7, ha="right")
    ax.set_xticks(xpos, STRATEGIES)
    ax.set_ylabel("Unsafe frequency")
    ax.set_ylim(0, 1.12)
    ax.legend(loc="upper left", fontsize=7.2)
    ax.set_title("what a solo evaluation can and cannot see", fontsize=8.8)
    panel_label(ax, "B")

    save(fig, outdir / "fig05_filter")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Figure 6: the safe face, its barrier and neutral drift
# --------------------------------------------------------------------------


def figure_safe_face(base, outdir: Path) -> pd.DataFrame:
    xs = np.linspace(0.0, 1.0, 400)
    barrier = np.array([safe_face_barrier(base, x) for x in xs])

    fig, axes = plt.subplots(1, 3, figsize=(11.0, 3.3))

    ax = axes[0]
    ax.plot(xs, barrier, color=PALETTE["CS"], lw=2.2)
    ax.set_yscale("log")
    ax.set_xlabel(r"share of conditional safety $x$ on the safe face")
    ax.set_ylabel(r"invasion barrier $L^{*}(x)$")
    ax.set_title("barrier of a mixed safe face", fontsize=8.6)
    ax.annotate(f"{barrier[0]:.1f}", (0.0, barrier[0]), textcoords="offset points",
                xytext=(12, 4), fontsize=7.5)
    ax.annotate(f"{barrier[-1]:.2f}", (1.0, barrier[-1]), textcoords="offset points",
                xytext=(-26, -12), fontsize=7.5)
    panel_label(ax, "A")

    ax = axes[1]
    ls = np.geomspace(0.3, 60.0, 400)
    crit = np.array([critical_cs_fraction(base, L) for L in ls])
    ax.plot(ls, crit, color=PALETTE["accent"], lw=2.2)
    ax.fill_between(ls, crit, 1.0, color=PALETTE["safe"], alpha=0.14)
    ax.fill_between(ls, 0.0, crit, color=PALETTE["unsafe"], alpha=0.14)
    ax.text(1.2, 0.28, "vulnerable", fontsize=8, color=PALETTE["unsafe"])
    ax.text(12, 0.72, "protected", fontsize=8, color=PALETTE["safe"])
    ax.set_xscale("log")
    ax.set_xlabel(r"effective liability $L$")
    ax.set_ylabel(r"critical share $x^{*}(L)$")
    ax.set_title("conditional safety required at each $L$", fontsize=8.6)
    panel_label(ax, "B")

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
    ax.axvline(xstar, color=PALETTE["unsafe"], ls="--", lw=1.1)
    ax.text(xstar - 0.03, 0.55, r"$x^{*}(L{=}5)$", rotation=90, fontsize=7,
            ha="right", color=PALETTE["unsafe"])
    ax.axvspan(0, xstar, color=PALETTE["unsafe"], alpha=0.10, lw=0)
    ax.set_xlabel(r"share of CS on the neutral safe face")
    ax.set_ylabel("stationary density (scaled)")
    ax.set_title("neutral drift on the safe face", fontsize=8.6)
    ax.legend(fontsize=7.2, loc="upper center")
    panel_label(ax, "C")

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

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.5))
    fig.subplots_adjust(wspace=0.42)
    for ax, data, yvals, ylabel, lab, show_cbar_label in [
        (axes[0], heat, betas, r"selection intensity $\beta$", "A", False),
        (axes[1], heat_z, zs, r"population size $Z$", "B", True),
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
        cbar.ax.tick_params(labelsize=6.5)
        if show_cbar_label:
            cbar.set_label(r"stationary $U^{*}$", fontsize=8)
        panel_label(ax, lab, dx=-0.20)
    axes[0].set_title(r"$Z=50$, varying selection intensity", fontsize=8.8)
    axes[1].set_title(r"$\beta=0.05$, varying population size", fontsize=8.8)
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

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5))
    ax = axes[0]
    ax.plot(sweep.liability_values, sweep.unsafe_forward, "-o", ms=2.6,
            color=PALETTE["safe"], label=r"$L$ decreasing, $z=0$ initially")
    ax.plot(sweep.liability_values, sweep.unsafe_backward, "-s", ms=2.6,
            color=PALETTE["unsafe"], label=r"$L$ increasing, capability diffused")
    ax.axvline(l_down, color=PALETTE["neutral"], ls="--", lw=0.7)
    ax.axvline(l_up, color=PALETTE["neutral"], ls="--", lw=0.7)
    ax.annotate("", xy=(l_up, 0.55), xytext=(l_down, 0.55),
                arrowprops=dict(arrowstyle="<->", lw=0.8, color=PALETTE["accent"]))
    ax.text(np.sqrt(l_down * l_up), 0.58,
            rf"$\times {l_up / l_down:.0f}$", ha="center", fontsize=7.5,
            color=PALETTE["accent"])
    ax.set_xscale("log")
    ax.set_xlabel(r"base effective liability $L$")
    ax.set_ylabel(r"long-run Unsafe frequency $U^{*}$")
    ax.set_title(f"hysteresis loop, area = {sweep.loop_area:.2f}", fontsize=8.6)
    ax.legend(fontsize=7.0, loc="center left")
    panel_label(ax, "A")

    ax = axes[1]
    ax.plot(sweep.liability_values, sweep.z_forward, "-o", ms=2.6,
            color=PALETTE["safe"], label=r"$L$ decreasing")
    ax.plot(sweep.liability_values, sweep.z_backward, "-s", ms=2.6,
            color=PALETTE["unsafe"], label=r"$L$ increasing")
    ax.set_xscale("log")
    ax.set_xlabel(r"base effective liability $L$")
    ax.set_ylabel(r"diffused capability stock $z$")
    ax.set_title("the ratchet variable never decreases", fontsize=8.6)
    ax.legend(fontsize=7.2, loc="center left")
    panel_label(ax, "B")

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
