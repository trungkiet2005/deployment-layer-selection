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
           "fig05_filter", "fig06_safe_face", "fig07_finite", "fig08_hysteresis"]


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
            "missing figures: " + ", ".join(missing) + "\nrun scripts/make_figures.py first"
        )

    tables = ROOT / "results" / "tables" / "tables.tex"
    if not tables.exists():
        raise SystemExit("missing results/tables/tables.tex; run scripts/run_analysis.py first")
    shutil.copy2(tables, ROOT / "paper" / "tables_generated.tex")
    print("staged", len(FIGURES), "figures and the generated tables")


def compile_pdf() -> None:
    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    proc = subprocess.run(cmd, cwd=ROOT / "paper", capture_output=True, text=True)
    sys.stdout.write(proc.stdout[-4000:])
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-4000:])
        raise SystemExit(f"latexmk failed with code {proc.returncode}")
    print("built", ROOT / "paper" / "main.pdf")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-compile", action="store_true")
    args = parser.parse_args()
    stage()
    if not args.no_compile:
        compile_pdf()
