# Referee report -- round 5 (JAAMAS pre-submission)

**Manuscript.** *Safe designs, unsafe ecosystems: deployment-layer selection in
an evolutionary AI race.* Springer `sn-jnl` package in `paper-jaamas/`,
generated from `paper/main.tex` by `scripts/build_jaamas.py`.

**Recommendation.** Accept after the corrections listed below. The contribution
is sound and well suited to this journal; the defects found are three
reproducibility bugs, two overstated propositions and a set of presentation
faults, none of which touches the four headline results. Every item marked
*fixed* has been corrected and re-verified in this repository; the items marked
*noted* are judgement calls left to the authors.

**Verification performed.** All twelve invasion thresholds, the barrier ratio,
the guard threshold, the assortment and misattribution closed forms, the probe
margins, the noise coefficients, the escape times, the robustness grid and the
hysteresis widths were recomputed from `src/dls/` and checked against the text.
The bibliography was checked one-to-one against the citations. The submission
package was compiled and inspected page by page.

---

## Summary of the contribution

The paper separates the payoff an agent earns in an interaction from the
payoff on which a principal decides whether to redeploy its design, calls the
difference the *selection wedge*, and shows that the wedge collapses to a
single effective liability `L = lambda h`. Every invasion condition is then
affine in `L`, so all thresholds are closed form. Four consequences follow: a
solo pre-deployment filter is dynamically inert; the safe face is
payoff-neutral while its invasion barrier varies by a factor of 77.7 along it;
long-run harm is non-monotone in liability over `(4.274, 42.765)`, because the
instrument taxes retaliation; and irreversible capability diffusion makes the
loss of a protected regime hysteretic with width `1/rho`.

This is a genuine addition to the evolutionary-game literature on AI races, and
the framing as a multi-agent-systems problem -- every existing instrument acts
from inside the interaction, this one acts on membership from outside -- is the
right one for this venue.

---

## Major issues

### M1. Two different estimators for the same observable *(fixed)*

`theory.longrun_unsafe_replicator` and `theory.matched_longrun_unsafe`
computed `U` of the **mean end state** rather than the **mean of** `U` over
end states, while `run_extensions.replicator_curve` and
`altdynamics.basin_average_unsafe` did it the other way round. Since `U` is
quadratic in `x` and the flow is bistable, these are not the same number: at
`L = 4.5` they differ by 0.326 against 0.301, and at `L = 20` by a factor of
two. Figures 3 and 5 and Corollary 10(iii) used the first estimator; every
extension table used the second.

The mean end state of a bistable flow is a composition the dynamics never
visits, so scoring it is not a defensible reading of "basin-averaged". Both
functions now integrate each start to its attractor, evaluate `U` there and
average, and both can return the Monte-Carlo standard error. Figures 3 and 5
were regenerated. `dynamics.average_replicator_attractor` now carries a
docstring warning against feeding its output to a non-linear observable, and
`tests/test_theory.py` gains a regression test that pins the difference rather
than only the value.

### M2. A non-converged grid point at the valley edge *(fixed)*

Figure 5 placed a marker at `L = L_dagger * (1 + 1e-9)`. At that liability the
transverse eigenvalue is of order `1e-8`, so the relaxation time is of order
`1e8` and the integration horizon of `t = 2000` reported a transient, not a
long-run value: the marker read about 0.235 where the right-limit is 0.319.
The offset is now `1e-3`, which puts the relaxation time at about `1e2`, and
the horizon is `2e4`. Section 2.4 now states this, and a second regression test
checks that doubling the horizon moves the reported value by less than
`5e-3`.

### M3. The same quantity reported as three different numbers *(fixed)*

The baseline replicator valley depth appeared as 0.299 in Table 5 (noise,
`eta = 0`), 0.299 in Table 7 (assortment, `r = 0`), 0.255 in Table 6 (charges,
linear) and 0.305 in the alternative-dynamics paragraph. Valley depth is a
largest-increase-over-a-grid statistic, so it is only comparable when the grid,
the number of starts and the lower cut are the same; the charge sweep used a
15-point grid, 40 starts and `l_min = 0.5` against the common 45-point grid, 48
starts and `l_min = 1.0`. The charge sweep now runs on the common grid
(extended to `L = 600`, which the convex charge needs, since its upper edge is
at 384.9) and the linear row reads 0.299, agreeing with the other two tables.
Table 6 and Figure 9C were regenerated; the window widths, which are closed
forms, did not change. Section 2.4 now states the rule.

### M4. Proposition 18 (was: "the rate at which twinning breaks") was wrong in
a way that matters *(fixed)*

The proposition assumed the perturbed fitness difference is constant along the
safe face, writing `x_dot = x(1-x) g` with a single `g`. It is not constant: it
is affine, and under execution noise the two ends differ substantially.
Richardson extrapolation on `eta` in `[1e-4, 1e-3]` gives

| end of the face | `delta a` | `delta m` | sign flips at |
|---|---|---|---|
| pure `AS` resident | `379.8 eta` | `8.000 eta` | `L = 47.5` |
| pure `CS` resident | `287.1 eta` | `46.00 eta` | `L = 6.24` |

The larger `delta m` at the conditional end is mechanical: between two copiers
a single tremble starts a cascade that runs to the end of the interaction,
whereas against an unconditionally safe partner it is mirrored once and dies.
The consequence is that the claim "noise converts neutrality into a strict
gradient pointing at the cheap-to-protect vertex" over "the entire
policy-relevant range" is false above `L = 6.24` -- which is most of the
liability valley. Above it the face settles at an interior coexistence, not at
the `CS` vertex.

The conclusion survives and is now stated in a stronger form. The settled
composition is

    x_hat(L) = (379.8 - 8 L) / (92.7 + 38 L),

independent of `eta` at leading order, and it exceeds the barrier share
`x*(L) = (42.765 - L)/(40.134 + 3.778 L)` at **every** `L >= 0`, because

    (379.8 - 8L)(40.134 + 3.778L) - (42.765 - L)(92.7 + 38L)
        = 7.776 L^2 - 418.6 L + 11278.6

has discriminant `-1.756e5 < 0` and minimum 5646. So execution noise always
moves the safe face to the protected side of its own invasion barrier, and by
the widest margin inside the valley (0.32 at `L_dagger`, 0.21 at `L = 10`).
This was confirmed against the exact noisy tables at `eta = 0.01, 0.02, 0.05`
over `L` in `[0, 40]`. The traversal time at `L = 0` is 17.8 rather than 15.5
time units at `eta = 1e-3`, since the affine field is slower than the constant
one it replaced. Table 1, Section 3.4 and the Discussion were updated to match.

### M5. Theorem 21 (hysteresis) omitted a hypothesis it needs *(fixed)*

The theorem asserted that the protected regime is lost at
`L_down = L*_{CAS->CS} = 0.551`. That is the barrier at the **pure conditional
vertex**, the lowest value it takes. Theorem 13 gives the barrier at a general
safe-face composition as `L*(x)`, which reaches 42.765 at the unconditional
vertex, so a population sitting there loses protection two orders of magnitude
higher on the `L`-axis. The numerics silently imposed the hypothesis by
starting the sweep at `x0 = (0.02, 0.96, 0.02)`, which is not stated in the
paper.

The theorem now carries the composition explicitly, `L_down = L*(x)` and
`L_up = L*(x')/rho`, and the paper notes that the width `1/rho` is a ratio and
therefore composition-free, that the loop is self-consistent after one
traversal because the safe face is always re-entered through `CS` (so
`x' = 1`), and that the sweep is run from a `CS`-dominated population for that
reason.

### M6. Corollary 17 (liability valley) called the whole safe face an attractor
*(fixed)*

Inside the valley only the segment `x >= x*(L)` of the safe face is protected;
below it a rare `CAS` grows. The corollary now says so, and carries a short
proof assembling Theorems 13 and 16. This is not a new result -- Section 3.4
already computes `x*(L)` -- but it was not connected to the bistability claim,
and a referee would read "two attractors" as "the whole face".

### M7. Corollary 10(iii) was quoted from a six-point grid *(fixed)*

"The basin-averaged long-run unsafe frequencies of the two pools agree to
within `1.2e-3` across the whole `L`-axis" came from
`results/tables/seed_sensitivity.csv`, which evaluates six liabilities
`{0, 0.3, 1, 5, 10, 45}`. On the 120-point grid the figure actually plots, the
largest gap is `6.2e-3`. The constant has been recomputed on that grid, and
`make_figures.figure_filter` now prints it so it cannot drift again.

Worth keeping in mind for the response letter: this bound is credible only
because the two curves are driven by the *same* Dirichlet draws. The
Monte-Carlo standard error of a single curve point inside the window is about
`2e-2`, an order of magnitude larger than the bound. Section 2.4 now says this
explicitly, because a referee who computes the standard error and not the
paired difference will otherwise conclude the claim is below the noise floor.

### M8. Basin-weighted quantities had no uncertainty and no stated measure
*(fixed)*

The headline "rising from 0 to 0.32" is the product of an exact attractor value
(0.465) with a basin volume, and a basin volume exists only relative to a
distribution over initial compositions. Recomputed with 20,000 draws the
figures are: basin volume `0.687 +/- 0.003`, product `0.319 +/- 0.002`. The
paper's 0.32 is therefore correct, but it is now reported with its standard
error and factorised, and the corollary is followed by a paragraph
distinguishing what depends on the uniform start measure from what does not.
Section 2.4 records the rule that any scalar depending on a basin volume is
recomputed with `2e4` draws.

---

## Minor issues

1. **Build lag in the bibliography** *(fixed)*. `paper-jaamas/build.py` ran
   `pdflatex, bibtex, pdflatex, pdflatex` while a `main.bbl` from the previous
   run sat beside the sources. `pdflatex` searches the working directory as
   well as the output directory and preferred the stale copy, so a change to
   `refs.bib` did not reach `main.pdf` until the *next* build, silently. This
   is the most dangerous defect in the repository for a submission workflow,
   because it produces a correct-looking PDF with an out-of-date reference
   list. `build.py` now removes the stale `.bbl` before the first run and
   copies the fresh one up after `bibtex`.

2. **`kolt2025governing` printed with no identifier** *(fixed)*.
   `normalise_bib.py` reshapes arXiv `@article` entries into `@misc` by
   appending a `note`, but this entry already had one ("Forthcoming, Notre Dame
   Law Review"). BibTeX keeps the first field of a repeated name and warned;
   the arXiv id and DOI were dropped. The two notes are now merged.

3. **Three proceedings titles printed in lower case** *(fixed)*.
   `refs_mas.bib`, the venue-specific supplement, was appended to the generated
   bibliography without passing through `normalise_bib.py`, so its `booktitle`
   fields were not brace-protected and the APA style sentence-cased them.
   Reference 60 read "proceedings of the 16th international conference on
   autonomous agents and multiagent systems" -- this journal's own conference,
   in a submission to this journal. All three are fixed and the whole
   bibliography is now normalised uniformly.

4. **Placeholder text in the compiled PDF** *(fixed)*. The acknowledgements
   block read "The authors thank [names] for comments on an earlier draft."
   Acknowledgements are optional and there are none, so the block is removed
   rather than left with a bracket in it. The two other `TODO BEFORE
   SUBMISSION` comments in `tail.tex` (funding, LLM use) were resolved into
   ordinary comments.

5. **Cover letter listed three of the four results** *(fixed)*. The abstract
   and the paper claim four; the letter omitted the neutral-face result. Added.

6. **A truncated label in Figure 1** *(fixed)*. Panel C listed the observables
   as "Unsafe frequency `U(x)`" and "Average Social", which is a truncation
   rather than a noun phrase. The figure has no source in the repository, so
   the text was edited in the PDF itself and now reads "Mean social payoff";
   the rest of the figure is byte-identical in appearance.

7. **The social functional is defined and never reported** *(fixed by
   wording)*. `pi_S` appears in equation (5), in Figure 1 and in Figure 2, and
   is then used only to define the wedge. A referee will ask why. The Model
   section now says: it is linear in the uncalibrated `h` and so carries a
   scale the model cannot supply, while the unsafe frequency is the same
   information without the weight.

8. **Bounds that the data do not tightly support** *(fixed)*.
   `L*_{CAS->AS}/B` has maximum 0.6149 on the grid, not 0.61; "over the whole
   grid it ranges from 4.4 to 90.4" excluded the six `p_max = 0.9` points where
   the ratio is negative, so it is now "over the eighteen grid points at which
   it is defined"; the seed-sensitivity bound of `4.2e-3` for seeds up to 20%
   is actually `2.8e-3` (`4.2e-3` is the 35% figure).

9. **Cross-reference slip** *(fixed)*. The Limitations paragraph said Sections
   3.7--3.8 bound three of the five limitations; the third is bounded in
   Section 3.9.

10. **Lagged enforcement claimed more than it proved** *(fixed)*. The argument
    shows that rest points are preserved and that the delayed characteristic
    equation reduces at `lambda = 0` to the undelayed one, hence no invasion
    threshold moves. It does not exclude a delay-induced oscillatory
    instability, which is a different mechanism; the text now says so.

11. **Proposition 19(i) overstated in the Discussion** *(fixed)*. "Zero-mean
    error changes nothing at all" is exact for the replicator field, the Nash
    set and the thresholds, all of which depend on the measurement only through
    its mean. The Fermi process compares realised payoffs through a non-linear
    imitation probability and does respond to the second moment. Both the
    proposition's follow-up paragraph and the Discussion now carry the
    qualification.

12. **The `GRIM` paragraph read as contradicting Section 3.7** *(fixed)*.
    "It moves no closed-form threshold at all" and "the edge sits between 12
    and 13 in the full pool" are about different objects -- the invasion
    thresholds computed from the `{AS, CS, CAS}` submatrix, and the edge of
    the harm curve for the whole pool. The paragraph now distinguishes them.

13. **A proof step attributed to the wrong lemma** *(fixed)*. In Proposition
    7(ii), "the only candidate is `CS`" follows from `AS` and `CAS` being in
    the support, not from Lemma 15; Lemma 15 supplies the *form* of the
    advantage. Both steps are now named.

14. **The interaction layer rests on a preprint** *(fixed by wording)*. A
    referee will raise this. The Model section now states it and says what
    depends on it: two matrices, from which every threshold is a closed form,
    so a revision of the source's constants moves the numbers and not the
    structure.

---

## Points noted but not changed

- **Reference list omits the ampersand before the final author** whenever an
  entry has three or more authors (92 of 134 entries). This is the behaviour of
  Springer's own `sn-apacite.bst`, which the package inherits unmodified apart
  from the three suppressed sorting passes: the bibliography style writes
  `no.and.before.last` on that branch. Since it is the stock template
  behaviour and Springer production re-typesets from the accepted source, we
  would not patch a Springer `.bst` for it. Worth one line in the cover letter
  if the authors want to pre-empt a copy-editing query.

- **Length.** 58 pages, 11 figures, 9 tables, 134 references. JAAMAS sets no
  limit and the robustness sections are what answer the obvious objections, so
  we would not cut the substance. If an editor asks, the two paragraphs that
  travel least with the argument are "Multi-player faces" and "Lagged
  enforcement", both of which would sit naturally in an appendix.

- **Figure 1 is typographically unlike the other ten.** It is a hand-drawn
  schematic in a heavy sans face at a larger optical size than the matplotlib
  figures, which share one width and one font scale. Its raster elements are
  395--4156 ppi, so print quality is not the issue; only consistency is.

- **`U(x)` in Figure 1 panel C sits hard against the right border of its box.**
  Pre-existing, not introduced by the label fix, and inside the box.

- **The basin measure is uniform on the simplex.** This is a statement of
  ignorance rather than an empirical claim, and is now labelled as such, but a
  referee is entitled to ask what an empirically motivated start measure would
  do to the 0.319. Nothing in the paper answers that; nothing in the paper
  needs to, since the attractor value and the thresholds are measure-free.

---

## What was verified and found correct

Recorded so that a later round does not re-audit ground already covered.

- All twelve entries of Table A1, and the four thresholds of equation (9),
  against `results/key_numbers.json` and a direct recomputation.
- `E[1/T] = 0.13206`, the payoff and unsafe-count matrices, and the unsafe
  frequency matrix.
- Theorem 13: `L*(0) = 42.765`, `L*(1) = 0.5506`, ratio 77.67; the critical
  shares `x*(1) = 0.951`, `x*(2) = 0.855`, `x*(5) = 0.640`, `x*(20) = 0.197`.
- Proposition 15: `p*(L) = (42.765 - L)/(24.165 + 8L)` on `(2.067, 42.765)`;
  `U = 0.4647` at the lower edge.
- Theorem 16: `L_dagger = 18.044/4.222 = 4.2739`.
- Proposition 14 (probes): the two-valued margin over all fifteen probe sets,
  and the sample sizes 7, 16, 111, 136 from the Bernoulli bound
  `n > (1.386/Delta)^2`.
- The structure-coefficient inequalities (23) and every number read off them
  (6.14, 3.14, 1.56, 2.93, 0.33, 1.10).
- The assortment closed form (24), the whole of Table 7, the closing
  assortment `r = 0.354` and the free-protection point `r = 0.076`.
- Proposition 20 and all of Table 8, including the window
  `10.006 (1 - 0.1053 q)/(1 - q)` and the barrier ratios 77.7, 85.3, 100.6,
  146.3.
- The robustness grid: window width in `[4.19, 12.79]` at all 24 points,
  barrier ratio 31.7 to 90.4 at `p_max = 0.6`, `L*_{CAS->AS} = 38.4` at
  `p_max = 0.9, B = 100`.
- Table 4 (escape times) and Table 9 (hysteresis) against
  `results/extensions.json`.
- The noise table, and the AS-end flip liabilities 44.3, 41.4, 34.4, 26.4.
- Bibliography: 134 entries, 134 cited, no orphans either way.
- Front matter: abstract 235 words (limit 150--250), 5 keywords (limit 4--6),
  no em-dashes, all 11 figures present and cited, zero overfull boxes, zero
  undefined references or citations, and all figure layout audits clean.

---

## Reproduction

```
python scripts/run_extensions.py          # or the charge sweep alone
python scripts/emit_extensions.py
python scripts/make_figures.py --only 4 5
python scripts/build_paper.py --no-compile
python scripts/check_layout.py
python scripts/build_jaamas.py
cd paper-jaamas && python build.py
python -m pytest tests -q
```
