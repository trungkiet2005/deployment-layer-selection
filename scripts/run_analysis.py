"""Reproduce every number and table reported in the manuscript.

Usage
-----
    python scripts/run_analysis.py [--outdir results]

Outputs
-------
``results/tables/*.csv``   machine-readable tables
``results/tables/*.tex``   LaTeX tables included by the manuscript
``results/key_numbers.json``  every scalar quoted in the text
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from dls.dynamics import (
    neutrally_stable_strategies,
    stationary_analysis,
    strict_nash_strategies,
)
from dls.functionals import build_functionals, build_selection_matrix, is_column_constant
from dls.race import STRATEGIES, RaceParams, build_race_tables
from dls.theory import (
    bistability_window_exact,
    critical_cs_fraction,
    evaluation_filter,
    face_equilibrium,
    guard_invasion_threshold,
    invasion_threshold,
    invasion_threshold_table,
    longrun_unsafe_replicator,
    longrun_unsafe_sml,
    safe_face_barrier,
    safe_face_is_neutral,
    solo_evaluation_scores,
)

P_MAX_TREATMENTS = (0.1, 0.6, 0.9)
BASELINE_P_MAX = 0.6


def matrix_frame(matrix: np.ndarray, strategies: tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame(matrix, index=list(strategies), columns=list(strategies))


def latex_matrix(
    matrix: np.ndarray, strategies: tuple[str, ...], caption: str, label: str, fmt: str = "%.3f"
) -> str:
    header = " & ".join(strategies)
    rows = [
        f"{s} & " + " & ".join(fmt % v for v in matrix[i]) + r" \\"
        for i, s in enumerate(strategies)
    ]
    body = "\n".join(rows)
    return (
        "\\begin{table}[htbp]\n\\centering\n"
        f"\\caption{{{caption}}}\n\\label{{{label}}}\n"
        "\\begin{tabular}{l" + "r" * len(strategies) + "}\n\\toprule\n"
        f" & {header} \\\\\n\\midrule\n{body}\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def main(outdir: Path) -> None:
    tables_dir = outdir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    key: dict[str, object] = {}
    tex_blocks: list[str] = []

    # ------------------------------------------------------------------
    # interaction layer: exact race tables for every treatment
    # ------------------------------------------------------------------
    race = {}
    for p_max in P_MAX_TREATMENTS:
        params = RaceParams(p_max=p_max)
        race[p_max] = build_race_tables(params)
        matrix_frame(race[p_max].payoff, STRATEGIES).to_csv(
            tables_dir / f"payoff_pmax{p_max}.csv"
        )
        matrix_frame(race[p_max].unsafe_count, STRATEGIES).to_csv(
            tables_dir / f"unsafe_count_pmax{p_max}.csv"
        )
        matrix_frame(race[p_max].unsafe_frequency, STRATEGIES).to_csv(
            tables_dir / f"unsafe_frequency_pmax{p_max}.csv"
        )

    base = race[BASELINE_P_MAX]
    key["expected_horizon"] = base.params.expected_horizon
    key["baseline_p_max"] = BASELINE_P_MAX
    key["safe_face_is_neutral"] = safe_face_is_neutral(base)

    tex_blocks.append(
        latex_matrix(
            base.payoff,
            STRATEGIES,
            caption=(
                "Task payoffs $a(i,j)$ of the reduced race game at "
                f"$p_r^{{\\max}}={BASELINE_P_MAX}$, computed exactly over the "
                "horizon distribution. Rows index the focal design."
            ),
            label="tab:payoff",
        )
    )
    tex_blocks.append(
        latex_matrix(
            base.unsafe_count,
            STRATEGIES,
            caption=(
                "Expected number of Unsafe actions $m(i,j)$ of the focal design at "
                f"$p_r^{{\\max}}={BASELINE_P_MAX}$."
            ),
            label="tab:unsafe-count",
        )
    )

    # equilibria of the interaction game itself (no liability)
    key["interaction_game_nss"] = {
        str(p): [STRATEGIES[i] for i in neutrally_stable_strategies(race[p].payoff)]
        for p in P_MAX_TREATMENTS
    }
    key["interaction_game_strict_nash"] = {
        str(p): [STRATEGIES[i] for i in strict_nash_strategies(race[p].payoff)]
        for p in P_MAX_TREATMENTS
    }

    # ------------------------------------------------------------------
    # the selection wedge
    # ------------------------------------------------------------------
    wedge_rows = []
    for lam in (0.0, 0.25, 0.5, 0.75, 1.0):
        fun = build_functionals(base, lam=lam, harm=10.0)
        wedge_rows.append(
            {
                "lambda": lam,
                "harm": 10.0,
                "effective_liability": fun.effective_liability,
                "wedge_frobenius_norm": float(np.linalg.norm(fun.wedge)),
                "strategically_inert": bool(is_column_constant(fun.wedge)),
            }
        )
    pd.DataFrame(wedge_rows).to_csv(tables_dir / "wedge.csv", index=False)
    key["wedge_inert_only_at_full_liability"] = all(
        r["strategically_inert"] == (r["lambda"] == 1.0) for r in wedge_rows
    )

    # ------------------------------------------------------------------
    # closed-form invasion thresholds
    # ------------------------------------------------------------------
    rows = []
    for th in invasion_threshold_table(base):
        rows.append(
            {
                "invader": th.invader,
                "resident": th.resident,
                "payoff_gain": th.payoff_gain,
                "harm_gain": th.harm_gain,
                "critical_liability": th.critical_liability,
                "direction": th.direction,
            }
        )
    inv_df = pd.DataFrame(rows)
    inv_df.to_csv(tables_dir / "invasion_thresholds.csv", index=False)

    tex_rows = []
    for r in rows:
        crit = "--" if r["critical_liability"] is None else f"{r['critical_liability']:.3f}"
        arrow = {
            "invades_below": r"$L<L^*$",
            "invades_above": r"$L>L^*$",
            "liability_independent": "--",
        }[r["direction"]]
        tex_rows.append(
            f"{r['invader']} & {r['resident']} & {r['payoff_gain']:.3f} & "
            f"{r['harm_gain']:.3f} & {crit} & {arrow} \\\\"
        )
    tex_blocks.append(
        "\\begin{table}[htbp]\n\\centering\n"
        "\\caption{Closed-form critical effective liabilities $L^{*}=\\delta a/\\delta m$ "
        "for every ordered invasion at $p_r^{\\max}=0.6$. The last column states when the "
        "invader has a positive growth rate.}\n\\label{tab:thresholds}\n"
        "\\begin{tabular}{llrrrl}\n\\toprule\n"
        "Invader & Resident & $\\delta a$ & $\\delta m$ & $L^{*}$ & invades \\\\\n\\midrule\n"
        + "\n".join(tex_rows)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )

    key["L_CAS_invades_AS"] = invasion_threshold(base, "CAS", "AS").critical_liability
    key["L_CAS_invades_CS"] = invasion_threshold(base, "CAS", "CS").critical_liability
    key["L_CS_invades_CAS"] = invasion_threshold(base, "CS", "CAS").critical_liability
    key["L_AS_invades_CAS"] = invasion_threshold(base, "AS", "CAS").critical_liability
    key["barrier_ratio_AS_over_CS"] = (
        key["L_CAS_invades_AS"] / key["L_CAS_invades_CS"]  # type: ignore[operator]
    )

    # ------------------------------------------------------------------
    # safe-face barrier and the critical share of conditional safety
    # ------------------------------------------------------------------
    xs = np.linspace(0.0, 1.0, 201)
    pd.DataFrame(
        {"cs_fraction": xs, "barrier": [safe_face_barrier(base, x) for x in xs]}
    ).to_csv(tables_dir / "safe_face_barrier.csv", index=False)
    key["critical_cs_fraction"] = {
        str(L): critical_cs_fraction(base, L) for L in (1.0, 2.0, 5.0, 10.0, 20.0)
    }

    # ------------------------------------------------------------------
    # bistability window and the liability valley
    # ------------------------------------------------------------------
    window = bistability_window_exact(base)
    key["guard_invasion_threshold"] = guard_invasion_threshold(base)
    key["bistability_window"] = list(window) if window else None
    if window:
        lo, hi = window
        eq_lo = face_equilibrium(base, "AS", "CAS", lo + 1e-6)
        key["unsafe_at_valley_entry"] = eq_lo.unsafe_frequency
        key["cas_fraction_at_valley_entry"] = eq_lo.fraction_second

    # ------------------------------------------------------------------
    # solo-evaluation filters
    # ------------------------------------------------------------------
    key["solo_evaluation_scores"] = solo_evaluation_scores(base)
    key["filters"] = {
        str(eps): list(evaluation_filter(base, eps)) for eps in (0.0, 0.05, 0.2, 0.5, 1.0)
    }

    filter_rows = []
    for eps, pool in [
        (1.0, evaluation_filter(base, 1.0)),
        (0.2, evaluation_filter(base, 0.2)),
        (0.05, evaluation_filter(base, 0.05)),
    ]:
        for L in (0.0, 0.3, 1.0, 3.0, 10.0, 45.0):
            filter_rows.append(
                {
                    "epsilon": eps,
                    "pool": "+".join(pool),
                    "effective_liability": L,
                    "unsafe_replicator": longrun_unsafe_replicator(
                        base, L, pool=pool, n_starts=120
                    ),
                    "unsafe_sml": longrun_unsafe_sml(base, L, pool=pool),
                }
            )
    pd.DataFrame(filter_rows).to_csv(tables_dir / "filter_futility.csv", index=False)

    # ------------------------------------------------------------------
    # equilibrium structure of the selection game across L
    # ------------------------------------------------------------------
    regime_rows = []
    for L in (0.0, 0.3, 1.0, 3.0, 5.0, 20.0, 45.0):
        m = build_selection_matrix(base, L)
        regime_rows.append(
            {
                "effective_liability": L,
                "strict_nash": "+".join(STRATEGIES[i] for i in strict_nash_strategies(m)),
                "nss": "+".join(STRATEGIES[i] for i in neutrally_stable_strategies(m)),
                "unsafe_replicator": longrun_unsafe_replicator(base, L, n_starts=120),
                "unsafe_sml": longrun_unsafe_sml(base, L),
            }
        )
    pd.DataFrame(regime_rows).to_csv(tables_dir / "regimes.csv", index=False)

    # ------------------------------------------------------------------
    # finite-population check with explicit mutation
    # ------------------------------------------------------------------
    finite_rows = []
    pool = ("AS", "CS", "CAS")
    sub = base.subset(pool)
    for L in (0.0, 1.0, 3.0, 5.0, 10.0, 45.0):
        pi_p = build_selection_matrix(sub, L)
        for Z in (50, 100):
            res = stationary_analysis(
                pi_p, sub.unsafe_frequency, population_size=Z, beta=0.05, mu=1.0 / Z
            )
            finite_rows.append(
                {
                    "effective_liability": L,
                    "Z": Z,
                    "beta": 0.05,
                    "mu": 1.0 / Z,
                    **{f"freq_{s}": f for s, f in zip(pool, res.strategy_frequencies)},
                    "unsafe": res.unsafe_frequency,
                }
            )
    pd.DataFrame(finite_rows).to_csv(tables_dir / "finite_population.csv", index=False)

    # ------------------------------------------------------------------
    # write outputs
    # ------------------------------------------------------------------
    (tables_dir / "tables.tex").write_text("\n".join(tex_blocks), encoding="utf-8")
    (outdir / "key_numbers.json").write_text(
        json.dumps(key, indent=2, default=float), encoding="utf-8"
    )
    print(json.dumps(key, indent=2, default=float))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("results"))
    args = parser.parse_args()
    main(args.outdir)
