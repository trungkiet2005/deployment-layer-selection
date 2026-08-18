"""Assemble and compile the manuscript from the generated results.

Copies the generated figures and LaTeX tables into ``paper/`` and runs
latexmk. Usage::

    python scripts/build_paper.py [--no-compile]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ["fig02_functionals", "fig03_simplex", "fig04_bifurcation",
           "fig05_filter", "fig06_safe_face", "fig07_finite", "fig08_hysteresis",
           "fig09_robustness", "fig10_generality"]


def stage() -> None:
    dest = ROOT / "paper" / "figures"
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in FIGURES:
        src = ROOT / "results" / "figures" / f"{name}.pdf"
        if not src.exists():
            missing.append(name)
            continue
        shutil.copy2(src, dest / f"{name}.pdf")
    if missing:
        raise SystemExit(
            "missing figures: "
            + ", ".join(missing)
            + "\nrun scripts/make_figures.py first"
            " (fig10_generality comes from scripts/emit_extensions.py)"
        )

    emitted = {
        "tables.tex": "tables_generated.tex",
        "tables_matchup.tex": "tables_matchup.tex",
        "tables_thresholds.tex": "tables_thresholds.tex",
        # written by scripts/emit_extensions.py
        "tab_noise.tex": "tab_noise.tex",
        "tab_charges.tex": "tab_charges.tex",
        "tab_hysteresis.tex": "tab_hysteresis.tex",
    }
    for name, target in emitted.items():
        src = ROOT / "results" / "tables" / name
        if not src.exists():
            producer = (
                "scripts/emit_extensions.py"
                if name.startswith("tab_")
                else "scripts/run_analysis.py"
            )
            raise SystemExit(f"missing results/tables/{name}; run {producer} first")
        shutil.copy2(src, ROOT / "paper" / target)
    print("staged", len(FIGURES), "figures and the generated tables")


def _run(cmd: list[str], allow_fail: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=ROOT / "paper", capture_output=True, text=True)
    if proc.returncode != 0 and not allow_fail:
        sys.stdout.write(proc.stdout[-6000:])
        sys.stderr.write(proc.stderr[-2000:])
        raise SystemExit(f"{cmd[0]} failed with code {proc.returncode}")
    return proc


def compile_pdf() -> None:
    """pdflatex/bibtex passes; latexmk needs perl, which MiKTeX may lack."""
    tex = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    _run(tex)
    _run(["bibtex", "main"], allow_fail=True)
    _run(tex)
    proc = _run(tex)

    log = (ROOT / "paper" / "main.log").read_text(encoding="utf-8", errors="ignore")
    warnings = [
        line for line in log.splitlines()
        if "Warning" in line and "Font" not in line and "hyperref" not in line.lower()
    ]
    for line in warnings[:25]:
        print("  ", line.strip())
    if not (ROOT / "paper" / "main.pdf").exists():
        raise SystemExit("no PDF produced")
    print("built", ROOT / "paper" / "main.pdf")
    _ = proc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-compile", action="store_true")
    args = parser.parse_args()
    stage()
    if not args.no_compile:
        compile_pdf()
