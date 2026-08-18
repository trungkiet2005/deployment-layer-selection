r"""Publication figure style and reusable plotting helpers.

Every figure in the manuscript is saved at exactly :data:`FIG_WIDTH` inches and
included at ``\linewidth``, so all figures are reduced by the same factor on the
page.  Font sizes are therefore comparable across figures and are drawn from the
single scale in :data:`FS` rather than chosen per panel.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

#: Width in inches of every saved figure.  The text block of the manuscript is
#: 6.27 in, so figures are reduced by 0.91 uniformly.
FIG_WIDTH = 6.9

#: The only font sizes used anywhere.  Values are points before the uniform
#: 0.91 reduction, so the smallest text on the page is about 6.4 pt.
FS = {
    "title": 9.5,   # panel titles
    "label": 9.0,   # axis labels, simplex vertex labels
    "tick": 8.0,    # tick labels
    "legend": 8.0,  # legend entries
    "annot": 7.5,   # in-axes annotations
    "tiny": 7.0,    # dense in-axes annotations (cell values, threshold marks)
}

#: Colour-blind-safe qualitative palette (Okabe-Ito).
PALETTE = {
    "AS": "#0072B2",
    "AU": "#D55E00",
    "CS": "#009E73",
    "CAS": "#CC79A7",
    "accent": "#E69F00",
    "neutral": "#4D4D4D",
    "grid": "#D9D9D9",
    "unsafe": "#B2182B",
    "safe": "#2166AC",
}

STRATEGY_LABEL = {
    "AS": "AS (always safe)",
    "AU": "AU (always unsafe)",
    "CS": "CS (conditionally safe)",
    "CAS": "CAS (conditionally antisocial safe)",
}


def use_paper_style() -> None:
    """Apply the manuscript figure style."""
    mpl.rcParams.update(
        {
            "figure.dpi": 160,
            "savefig.dpi": 400,
            # a fixed saved size is what keeps the on-page scale uniform, so the
            # bounding box must not be cropped to the ink
            "savefig.bbox": None,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Times New Roman", "STIXGeneral"],
            "mathtext.fontset": "stix",
            "font.size": FS["label"],
            "axes.titlesize": FS["title"],
            "axes.labelsize": FS["label"],
            "legend.fontsize": FS["legend"],
            "xtick.labelsize": FS["tick"],
            "ytick.labelsize": FS["tick"],
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": PALETTE["grid"],
            "grid.linewidth": 0.5,
            "grid.alpha": 0.8,
            "lines.linewidth": 1.5,
            "legend.frameon": False,
            "legend.handlelength": 2.0,
            "legend.columnspacing": 1.1,
            "legend.borderaxespad": 0.2,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 2.6,
            "ytick.major.size": 2.6,
            "xtick.major.pad": 2.0,
            "ytick.major.pad": 2.0,
            "axes.labelpad": 2.5,
        }
    )


def new_figure(height: float, *, nrows: int = 1, ncols: int = 1, **kwargs):
    """A constrained-layout figure of the standard width.

    Constrained layout fits the decorations inside a *fixed* canvas, which is
    what lets every figure keep the same saved width.
    """
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(FIG_WIDTH, height), layout="constrained", **kwargs
    )
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.02, wspace=0.03, hspace=0.03)
    return fig, axes


def save(fig: plt.Figure, path: Path | str, also_png: bool = True) -> None:
    """Write a figure as PDF (and optionally PNG) and close it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"))
    if also_png:
        fig.savefig(path.with_suffix(".png"))
    plt.close(fig)


def panel_label(ax: plt.Axes, text: str, dx: float = -0.16, dy: float = 1.06) -> None:
    """Place a bold panel label in axes coordinates."""
    ax.text(
        dx,
        dy,
        text,
        transform=ax.transAxes,
        fontsize=FS["title"],
        fontweight="bold",
        va="top",
        ha="left",
    )


def panel_title(ax: plt.Axes, letter: str, text: str = "",
                size: float | None = None, pad: float = 5.0) -> None:
    """Left-aligned title carrying its own bold panel letter.

    Keeping the letter inside the title avoids the collisions that occur when a
    separate label is placed in axes coordinates next to a centred title.
    """
    label = rf"$\bf{{{letter}}}$" + (f"   {text}" if text else "")
    ax.set_title(label, loc="left", fontsize=size or FS["title"], pad=pad)
