r"""Audit every generated figure for text collisions.

A legend sitting on a curve, an annotation over the data it points at, or a
label pushed off the canvas are invisible in the vector output until the figure
is on the page.  :mod:`dls.layout_check` finds them mechanically; this script
renders each figure and runs that audit, so the check does not depend on
noticing the collision by eye.

The builders are called in process and their ``save`` is replaced by a spy, so
nothing is written to ``results/`` and the audit sees the live figure rather
than a PDF.

Usage
-----
    python scripts/check_layout.py [--quick] [--only 6 10]

``--quick`` uses the coarse grids the builders offer.  It is much faster and
finds the same collisions in practice, but the figures that ship are built
without it, so a clean full run is what counts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dls.plotting as plotting                                   # noqa: E402
from dls.layout_check import audit                                # noqa: E402
from dls.plotting import use_paper_style                          # noqa: E402
from dls.race import RaceParams, build_race_tables                # noqa: E402

CAPTURED: dict[str, object] = {}


def _spy(fig, path, also_png=True) -> None:
    CAPTURED[Path(path).stem] = fig


def build_all(quick: bool = False, only: list[str] | None = None) -> dict:
    """Render the generated figures and return them by name."""
    plotting.save = _spy
    import emit_extensions
    import emit_round4
    import make_figures

    make_figures.save = _spy
    emit_extensions.save = _spy
    emit_round4.save = _spy

    use_paper_style()
    base = build_race_tables(RaceParams(p_max=make_figures.BASELINE_P_MAX))
    out = ROOT / "results" / "figures"          # never written: save is a spy

    ext = json.loads((ROOT / "results" / "extensions.json").read_text(encoding="utf-8"))
    round4 = json.loads((ROOT / "results" / "round4.json").read_text(encoding="utf-8"))

    jobs = {
        "2": lambda: make_figures.figure_functionals(base, out),
        "3": lambda: make_figures.figure_simplex(base, out),
        "4": lambda: make_figures.figure_bifurcation(base, out, quick),
        "5": lambda: make_figures.figure_filter(base, out, quick),
        "6": lambda: make_figures.figure_safe_face(base, out),
        "7": lambda: make_figures.figure_finite(base, out, quick),
        "8": lambda: make_figures.figure_hysteresis(base, out, quick),
        "10": lambda: emit_extensions.figure_generality(ext, out),
        "11": lambda: emit_round4.figure_observation(round4, out),
    }
    CAPTURED.clear()
    for key in only or list(jobs):
        print(f"  building figure {key} ...", flush=True)
        jobs[key]()
    return dict(CAPTURED)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()

    figures = build_all(quick=args.quick, only=args.only)
    failures = 0
    for name in sorted(figures):
        collisions = audit(figures[name])
        status = "clean" if not collisions else f"{len(collisions)} collision(s)"
        print(f"{name}: {status}")
        for collision in collisions:
            print(f"    {collision}")
        failures += len(collisions)
    print("total collisions:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
