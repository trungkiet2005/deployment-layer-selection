"""Publication figure style and reusable plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

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
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Times New Roman", "STIXGeneral"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.titlesize": 9.5,
            "axes.labelsize": 9,
            "legend.fontsize": 7.8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": PALETTE["grid"],
            "grid.linewidth": 0.5,
            "grid.alpha": 0.8,
            "lines.linewidth": 1.5,
            "legend.frameon": False,
            "xtick.direction": "out",
            "ytick.direction": "out",
        }
    )


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
        fontsize=10.5,
        fontweight="bold",
        va="top",
        ha="left",
    )


def panel_title(ax: plt.Axes, letter: str, text: str = "", size: float = 8.6,
                pad: float = 7.0) -> None:
    """Left-aligned title carrying its own bold panel letter.

    Keeping the letter inside the title avoids the collisions that occur when a
    separate label is placed in axes coordinates next to a centred title.
    """
    label = rf"$\bf{{{letter}}}$" + (f"   {text}" if text else "")
    ax.set_title(label, loc="left", fontsize=size, pad=pad)
