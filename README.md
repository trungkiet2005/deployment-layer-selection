# Deployment-Layer Selection in Evolutionary AI-Race Dynamics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![EGTtools](https://img.shields.io/badge/built%20with-EGTtools-brightgreen.svg)](https://github.com/Socrats/EGTTools)

Reproduction code for a study of what happens when the layer at which an AI
design *acts* is separated from the layer at which it is *selected*.

In classical evolutionary game theory the payoff an individual earns in the
game is the same quantity that governs its reproduction.  In an ecosystem of
deployed AI agents this identity breaks.  An agent earns payoffs in an
interaction, but whether its *design* is replicated is decided by a principal
who is not a player in that interaction and who internalises only part of the
harm the design causes.  We call the resulting difference between the
selection functional and the social functional the **selection wedge**, and we
study the evolutionary dynamics it induces.

The interaction layer is the repeated two-player AI race of
Fernández Domingos & Han (2026), with the reduced strategy set
AS / AU / CS / CAS.

## Headline results

| | Result |
|---|---|
| **1** | Only the product `L = λh` of liability pass-through and per-action harm enters the dynamics. Every invasion condition is affine in `L`, giving closed-form thresholds `L* = δa / δm`. |
| **2** | **Solo safety evaluations are futile.** A filter that rejects any design whose Unsafe frequency against a safe environment exceeds `ε` rejects AU and admits CAS, whose self-play Unsafe frequency is 1. Removing AU leaves the equilibrium Unsafe frequency unchanged. |
| **3** | **Conditional safety is 78x harder to invade than unconditional safety.** Repelling CAS from an all-AS population needs `L > 42.77`; from an all-CS population, `L > 0.55`. The safe face AS-CS is *exactly payoff neutral*, so this barrier is set by a neutrally drifting variable. |
| **4** | **Long-run harm is not monotone in liability.** For `L ∈ (4.27, 42.77)` the system is bistable: liability penalises the retaliation that conditional safety relies on, so a protected population becomes only one of two attractors. Raising `L` from 4.2 to 4.5 raises the basin-averaged Unsafe frequency from 0 to ≈ 0.32. |
| **5** | **The ratchet makes it worse.** Coupling the dynamics to a non-decreasing stock of diffused capability that erodes enforcement by a factor `θ` produces hysteresis: the liability needed to *recover* a safe regime is `1/(1-θ)` times the liability at which it was lost — a factor of 10 at `θ = 0.9`. |

## Installation

```bash
git clone https://github.com/<user>/deployment-layer-selection.git
cd deployment-layer-selection
pip install -e .[dev]
```

Requires Python ≥ 3.10, `numpy`, `scipy`, `matplotlib`, `pandas` and
[`egttools`](https://github.com/Socrats/EGTTools) ≥ 0.1.14.

## Reproducing the paper

```bash
python scripts/run_analysis.py --outdir results   # tables + every quoted number
python scripts/make_figures.py                    # Figures 2-8
pytest                                            # 30 checks of the analytics
```

`scripts/make_figures.py --quick` runs a coarser sweep in about a minute.
Everything is deterministic: the only randomness is the choice of initial
conditions for basin averaging, which is seeded.

Outputs:

```text
results/key_numbers.json     every scalar quoted in the manuscript
results/tables/*.csv         payoff, harm, threshold and sweep tables
results/tables/tables.tex    LaTeX tables included by the manuscript
results/figures/fig0*.pdf    publication figures
```

## Package layout

```text
src/dls/
  race.py         exact evaluation of the reduced race game over the horizon law
  functionals.py  task, selection and social payoff functionals; the wedge
  dynamics.py     replicator, replicator-mutator, finite-population Fermi process
  theory.py       closed-form thresholds, face equilibria, evaluation filters
  ratchet.py      coupled (x, z) eco-evolutionary system and hysteresis sweeps
  plotting.py     figure style
```

### A note on the interaction layer

The four reduced strategies are deterministic, so the action path of an
ordered pair is fixed once the pair is fixed and the only stochastic primitive
is the horizon `T`.  We therefore evaluate every matchup by **exact
expectation over the horizon distribution** instead of Monte Carlo sampling.
This removes simulation noise from the payoff matrix entirely, which matters
here because several thresholds are ratios of small payoff differences.
`tests/test_race.py` checks the exact values against a 200 000-draw simulation.

## Citing

If you use this code, please cite both this repository and the toolbox it is
built on:

> Fernández Domingos, E., Santos, F. C. & Lenaerts, T. *EGTtools: Evolutionary
> game dynamics in Python.* iScience **26**, 106419 (2023).

The interaction layer is adapted from:

> Fernández Domingos, E. & Han, T. A. *Falling Behind Drives Unsafe Development
> in an Idealised AI Race Experiment.* arXiv:2607.26034 (2026).

## License

MIT — see [LICENSE](LICENSE).
