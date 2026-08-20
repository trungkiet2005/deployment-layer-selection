# Deployment-Layer Selection in Evolutionary AI-Race Dynamics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![EGTtools](https://img.shields.io/badge/built%20with-EGTtools-brightgreen.svg)](https://github.com/Socrats/EGTTools)
[![tests](https://img.shields.io/badge/tests-91%20passing-success.svg)](tests/)

Reproduction code for a study of what happens when the layer at which an AI
design *acts* is separated from the layer at which it is *selected*.

In classical evolutionary game theory the payoff an individual earns in the
game is the same quantity that governs its reproduction. In an ecosystem of
deployed AI agents that identity breaks. An agent earns payoffs in an
interaction, but whether its *design* is replicated is decided by a principal
who is not a player in that interaction and who internalises only part of the
harm the design causes. We call the resulting difference between the selection
functional and the social functional the **selection wedge**, and study the
evolutionary dynamics it induces.

The interaction layer is the repeated two-player AI race of
Fernández Domingos & Han (2026), with the reduced strategy set
AS / AU / CS / CAS.

## Headline results

| | Result |
|---|---|
| **1** | Only the product `L = λh` of liability pass-through and per-action harm enters the dynamics. Every invasion condition is affine in `L`, giving closed-form thresholds `L* = δa / δm`. |
| **2** | **Solo safety evaluations are dynamically empty.** CAS weakly dominates AU at every `L`, so a filter that rejects designs by their behaviour against a safe environment removes only a weakly dominated design. The one attractor it deletes carries the maximal harm `U = 1`, which the surviving pool reproduces; on a common start measure the long-run unsafe frequency is unchanged to within `1.2e-3`. |
| **3** | **Conditional safety is 78x cheaper to protect than unconditional safety.** Repelling CAS from an all-AS population needs `L > 42.77`; from an all-CS population, `L > 0.55`. The AS–CS face is *exactly payoff neutral*, so this barrier is set by a neutrally drifting variable. At `p_max = 0.9` conditional safety needs no liability at all. |
| **4** | **Long-run harm is not monotone in liability.** For `L ∈ (4.27, 42.77)` the system is bistable: liability taxes the retaliation that conditional safety relies on. Raising `L` from 4.2 to 4.5 raises the basin-averaged unsafe frequency from 0 to ≈ 0.32. A window of this kind exists at **every** prize and risk level tested (24/24 grid points), with multiplicative width 4.2–12.8. |
| **5** | **The valley is long-lived, not an artefact of the deterministic limit.** In a finite population the mean escape time from the unsafe attractor at `L = 10` ranges from 65 generations (`Z=30, β=0.02`) to `3.9e13` generations (`Z=100, β=0.2`). |
| **6** | **The ratchet makes it worse.** Coupling to a non-decreasing stock of diffused capability that erodes enforcement to a residual fraction `ρ` produces hysteresis of width exactly `1/ρ`, independent of the diffusion rate — a factor of 10 at `ρ = 0.1`. |
| **7** | **The mechanisms are not artefacts of the modelling choices.** They are inherited by any imitative payoff-monotone dynamics, and the best-response bifurcation sits at the same threshold. They survive four non-linear liability schedules, three further conditional designs, and execution noise up to about 5%; the valley closes at 7.5% error, but only because a conditionally safe population stops being safe. Two of the four carry over exactly to arbitrary population structure. |
| **8** | **Probe your agent against a reciprocating counterpart.** Over all fifteen probe sets the separating margin takes exactly two values: 0.539 when the probe set contains a conditional design and no always-unsafe one, and 0.132 otherwise. A hostile probe is *worse* than a gentle one, because conditional safety retaliates against it in 87% of rounds and is scored as unsafe. At equal confidence the reciprocating probe needs 7 evaluation episodes where the solo probe needs 111. |
| **9** | **Network reciprocity shrinks the valley, entirely from above.** Under assortative matching at level `r` the guard threshold is *exactly* independent of `r`, because the assortment correction is a self-interaction term and the two designs it compares are self-identical. The upper edge falls as `(42.765 - 74.565 r) / (1 + 8 r)`, so the window narrows from 10.0 to 1.4 at `r = 0.3` and closes at `r = 0.354`. |
| **10** | **Only one kind of measurement error matters: who gets blamed.** Zero-mean error in counting incidents, a flat charge per deployment, and any error depending only on the counterparty are all absorbed *exactly*; systematic under-reporting merely relabels the liability axis. Booking a fraction `q` of the blame against the wrong party is the exception: `L*` for protecting unconditional safety scales as `1/(1-q)`, because the design a first strike exploits has by construction a spotless record. At `q = 0.5` the dangerous range doubles. |

## Installation

```bash
git clone https://github.com/<user>/deployment-layer-selection.git
cd deployment-layer-selection
pip install -e ".[dev]"
```

Requires Python ≥ 3.10, `numpy`, `scipy`, `matplotlib`, `pandas` and
[`egttools`](https://github.com/Socrats/EGTTools) ≥ 0.1.14.

## Reproducing the paper

```bash
python scripts/run_analysis.py --outdir results    # tables + every quoted number
python scripts/run_robustness.py --outdir results  # prize/risk sweep, escape times
python scripts/run_extensions.py                   # noise, pools, dynamics, charges
python scripts/emit_extensions.py                  # their tables and fig10_generality
python scripts/run_round4.py                       # attribution, assortment, lag, grim
python scripts/emit_round4.py                      # their tables and fig11_observation
python scripts/make_figures.py                     # the other figures
python scripts/check_layout.py                     # no text on a curve or off the canvas
python scripts/build_paper.py                      # stage figures, run pdflatex/bibtex
pytest                                             # 95 checks of the analytics and the layout
```

`scripts/make_figures.py --quick` runs a coarser sweep in about a minute, and
`--only 4 5` rebuilds a subset. Every figure is saved at the same width
(`dls.plotting.FIG_WIDTH`) with an uncropped bounding box and is included at
`\linewidth`, so all figures are reduced by the same factor on the page and
their text renders at the same size; `tests/test_figures.py` enforces this.
`scripts/check_layout.py` renders every figure and reports any legend sitting
on a curve, text over text, or label pushed off the canvas, which is the class
of fault that survives visual inspection and only shows up on the page; the
same audit runs in `tests/test_figures.py` for the figures that are cheap to
rebuild. Everything is deterministic: the only
randomness is the choice of initial conditions for basin averaging, which is
seeded.

Outputs:

```text
results/key_numbers.json         every scalar quoted in the manuscript
results/robustness_summary.json  prize/risk sweep, escape times, seed sensitivity
results/extensions.json          noise, pools, dynamics, charges, probes, ratchet
results/round4.json              measurement channel, assortment, lag, grim trigger
results/tables/*.csv             payoff, harm, threshold and sweep tables
results/tables/tables.tex        LaTeX tables included by the manuscript
results/figures/fig0*.pdf        publication figures
paper/main.pdf                   the compiled manuscript
```

## Package layout

```text
src/dls/
  race.py         exact evaluation of the reduced race game over the horizon law
  functionals.py  task, selection and social payoff functionals; the wedge
  dynamics.py     replicator, replicator-mutator, finite-population Fermi process
  theory.py       closed-form thresholds, face equilibria, evaluation filters
  ratchet.py      coupled (x, z) eco-evolutionary system and hysteresis sweeps
  robustness.py   thresholds across prize and risk, escape times, erosion channels
  noisy.py        stochastic finite-state designs under trembling-hand noise
  altdynamics.py  logit, best-response and aspiration dynamics
  charges.py      non-linear liability schedules and their thresholds
  probes.py       probe-set evaluation filters and their separating margins
  observation.py  imperfect measurement of the externality; lagged enforcement
  assortment.py   assortative matching and what it does to the bistable window
  plotting.py     figure style: one saved width and one font scale for all
```

### A note on the interaction layer

The four reduced strategies are deterministic, so the action path of an
ordered pair is fixed once the pair is fixed and the only stochastic primitive
is the horizon `T`. We therefore evaluate every matchup by **exact expectation
over the horizon distribution** instead of Monte Carlo sampling. This removes
simulation noise from the payoff matrix entirely, which matters here because
several thresholds are ratios of small payoff differences.
`tests/test_race.py` checks the exact values against a 200 000-draw simulation.

The same exactness is kept when designs are made stochastic. `noisy.py`
propagates the joint chain over the two internal states against the horizon
law, carrying the progress difference and the unsafe count as state and the
accumulated stage payoff as a first moment, which the setback probability
requires because it multiplies the kept payoff. At zero noise it reproduces
the deterministic tables to `1.1e-6`, which is the horizon truncation.

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
