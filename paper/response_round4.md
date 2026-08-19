# Response to the reviewer -- round 4

**Manuscript:** *Safe designs, unsafe ecosystems: deployment-layer selection in an
evolutionary AI race*

We thank the reviewer for a report whose questions were, once again, more useful
than the recommendation. All six questions have been answered with new analysis
rather than with argument, and two of them changed a result rather than
confirming one. The revision adds one results section (§3.9 *What the principal
can see*), one new paragraph of results in each of §3.7 and §3.8, four new
propositions, two tables, one figure, two new code modules and 23 new tests
(91 in total, all passing).

We begin with the two answers that are substantive, then work through the report
in its own order.

## The two answers that changed something

**1. Only one kind of measurement error matters, and it is not the kind one
would guard against.** Asked what happens when the principal observes noisy
proxies of `m` (Q2), we found a clean separation. Zero-mean measurement error is
*exactly* inert, because the selection functional is affine in the charge base
and a design meets the population rather than one realisation of it. A flat
charge per deployment is exactly inert by column-constant invariance. Any error
that depends only on the counterparty is exactly inert for the same reason.
Systematic under-reporting is not inert but is harmless in a precise sense: it
relabels the liability axis, so a regime that books one incident in three is the
regime at one third of the nominal liability, and no ratio in the paper moves.
The exception is attribution. If a fraction `q` of the blame for an interaction
is booked against the wrong party, then

    L*(CAS into AS)(q) = L*(CAS into AS)(0) / (1 - q),

which diverges as `q -> 1`, while the guard threshold moves by at most 11.8%
over the whole range. The reason is a single sentence: the design that a first
strike exploits is by construction the design with a spotless record, so blame
moved onto it is blame destroyed. Misattribution is therefore a subsidy to
initiation specifically, it widens and deepens the liability valley (a factor of
19.0 at `q = 0.5`, against 10.0 at `q = 0`), and it leaves the protection of
conditional safety essentially untouched (`L*(CAS into CS)` moves only from
0.551 to 0.623 across all `q`). This is new Proposition 20 and Proposition 21 in
§3.9, with Table 8 and Figure 10A-B.

The policy consequence inverts the usual emphasis, and we state it that way in
§4: the budget for an incident-reporting standard should be spent on
identifying the initiator, not on measuring severity.

**2. The valley question we left open is now closed, and the answer is the
opposite of a worry.** Asked whether network reciprocity expands or shrinks the
bistable window (Q3), we found that the previous version had left it open for a
reason that was fixable. The structure coefficient of Tarnita et al. orders each
*pair* of designs, and a bistable pair has no order, so it cannot reach the
valley. Assortative matching can, because it keeps the dynamics: at assortment
`r` the population plays the ordinary matrix game

    pi~(i,j) = r pi_P(i,i) + (1 - r) pi_P(i,j),

which is still affine in `L`, so every closed form of the paper survives. Two of
the three consequences are exact.

* The safe face is an exact twin face at every `r`, because the assortment
  correction is a self-interaction term and AS and CS are self-identical.
* **The guard threshold does not move at all.** `L-dagger = 4.274` for every
  `r`, because the assortment correction contributes zero to both the numerator
  and the denominator of the comparison behind it. The lower edge of the valley
  is immune to population structure.
* The upper edge is `(42.765 - 74.565 r) / (1 + 8 r)`, which falls to zero at
  `r = 0.574`.

So the window narrows monotonically and entirely from above -- 10.0, 6.5, 4.6,
2.5, 1.4 at `r = 0, 0.05, 0.10, 0.20, 0.30` -- and closes at `r = 0.354`. The
valley depth follows: 0.299, 0.216, 0.160, 0.060, 0.008, and exactly 0 at
`r = 0.40`. This is the new *Assortative matching* paragraph in §3.8, with
eq. (20), Table 7 and Figure 10C-D, and it replaces the sentence in which we
previously declined to settle the question.

---

## Weaknesses

### W1. Stylized four-strategy two-player race; no market competition, gradual capability, learning

We accept the framing and have not tried to remove it, because the paper's claim
is about a mechanism rather than about a calibrated ecosystem, and the mechanism
is what the reduced race isolates. What we have done in this round is to state
the boundary more honestly and to test one more of the excluded features. §3.7
now contains a fifth design, a grim trigger, chosen because it is the extreme
point of the retaliation axis: it never forgives. Its effect on the closed forms
is nil, because it leaves the {AS, CS, CAS} submatrix untouched and every
threshold is computed from that submatrix. Its effect on the basins is
substantial and safe-directed, cutting the valley depth from 0.299 to 0.163, and
to 0.109 when a two-round punisher is present as well. Its effect under
execution noise is the opposite, and is the interesting part: a single tremble is
permanent, so a grim population is unsafe in 7.6% of rounds at `eta = 0.01` and
28.9% at `eta = 0.05`, against 4.7% and 18.6% for the copier. Harsher
retaliation is a better guard and a worse citizen, and the error rate decides
which effect dominates.

Market competition and learning remain out of scope and are named as such in the
limitations.

### W2. L is uncalibrated; mapping real regimes to L and measuring m is nontrivial

The calibration half of this was addressed in the previous round (§4, *Reading
the liability axis*: the axis in prize units, thresholds at `L/B = 0.0012`,
0.0055, 0.043, 0.428, and a comparative statement that needs no estimate of
`h`). We continue to decline a point calibration for the reason the reviewer
anticipates.

The measurement half is the new §3.9 and is summarised above. We would draw
attention to what it does for the calibration problem: three of the four ways of
mismeasuring `m` cost nothing, so the practical objection "we cannot measure
`m`" is weaker than it looks. What one has to measure is not the amount of harm
but its author.

### W3. Neutrality of the safe face may be fragile

It is fragile, and we now say exactly how fragile, which is Q1 and is answered
below. In one line: neutrality breaks at first order in any twinning error, the
face is then traversed in time `Theta(1/eta)`, and a tremble rate above
`5.3 x 10^-4` is enough for selection to beat drift in a population of 100. We
have rewritten the surrounding claim accordingly: the neutral face is the
limiting case of a slow directed drift, not a description of a real ecosystem.
The direction of that drift is towards the protected vertex, so the fragility
runs in the reassuring direction, and misattribution does not disturb it at all
(the face is an exact twin face for every `q`).

### W4. Limited detail on networked populations and path-dependent institutions

Networked populations: answered in W2 above and in Q3 below, with an exact
result rather than a conjecture.

Path-dependent institutions: §3.10 (the ratchet) is the path-dependence result
and was generalised to a class of erosion channels in the previous round. We
have not extended it further, and we now say what the remaining assumption is
and who would have to relax it: the attribution weight `q` of §3.9 is exogenous
in our model, whereas in a real regime it is contested by the parties it
charges. A model in which principals litigate attribution rather than accept it
is the natural next paper, and we say so in the limitations rather than
gesturing at it.

### W5. Finite-population analysis could probe wider ranges

We have added the one sweep that changes an interpretation rather than adding a
row to a table: the drift-versus-selection crossover on the safe face,
`beta Z g > 1`, which at the paper's baseline `beta = 0.05`, `Z = 100` gives
`eta* = 5.3 x 10^-4` (Proposition 19 and the paragraph after it). This is what
tells a reader when the finite-population drift story in §3.3 applies at all,
and the answer is: only in ecosystems with essentially no execution error. We
judged that more informative than widening the existing mutation and intensity
sweeps, whose qualitative message is already reported.

### W6. Evaluation filters modelled as thresholds on unsafe frequency are simple

Agreed, and we have made the model earn that simplicity in the one direction the
reviewer's Q4 asks about. §3.7 now converts the separating margin into the
quantity an evaluator actually budgets, the number of probe episodes: at 95%
confidence with the Bernoulli bound, the reciprocating probe needs `n >= 7`
episodes at `eta = 0` and `n >= 16` at `eta = 0.05`, where the solo probe needs
`n >= 111` and `n >= 136`. Multi-dimensional and context-dependent evaluation is
still outside the model, and we do not claim otherwise.

### W7. Up-front scoping of which conclusions rely on the extensions

This was a fair criticism and we have acted on it directly. Section 3 now opens
with Table 3, which sorts every claim of the paper into *general* (a statement
about symmetric matrix games or about selection functionals as such), *exact,
this race* (form general, constants not), and *numerical* (established by
sweeping a grid). The introduction's limitations paragraph has been rewritten to
name all four modelling choices and to say which section relaxes each, with the
headline of each relaxation stated there rather than only in §3.

### W8. Narrative interleaves general results with one parameterisation's numbers

Same fix. Table 3 is designed exactly for a reader tracking generality against
instance, and it names the baseline parameterisation in its caption so the
instance-specific numbers are attributable at a glance.

### W9. Missing related work: principal-agent with imperfect observables; sanctioning with institutional noise

Added as a new paragraph in §1.1, *Selection on an imperfect measure*, with
three references: Holmstrom (1979) on informativeness, and Baker (1992) and
Holmstrom & Milgrom (1991) on distorted performance measures and multitasking.
The connection is closer than a citation: the liability charge is a distorted
performance measure in exactly Baker's sense, and the valley is the multitask
distortion at a different level. We also state the two differences, because they
are what makes the result new rather than a restatement. The reallocation here
is evolutionary rather than deliberate, so the distortion appears with no
optimising agent to attribute it to; and because the distortion is bistable, the
loss is discontinuous in the power of the instrument rather than smooth, which
the static second-best theory does not predict.

On sanctioning and second-order free riders we already cite Sigmund et al.
(2010), Wang et al. (2019) and Panchanathan & Boyd (2004), and the new §3.9 is
in effect the institutional-noise analysis for our instrument, so we have not
added further references there. We have also not padded the empirical section:
beyond Fernandez Domingos & Han and the multi-agent risk survey we already cite,
we are not aware of experiments that would bear on the retaliation-as-guard
mechanism specifically, and we prefer to say so.

---

## Questions

### Q1. Robustness of neutrality to departures from exact twinning; a perturbation analysis

New Proposition 19 in §3.7. Perturb the face so that a rare CS in an AS resident
grows at `g = delta_a - L delta_m` instead of zero. The replicator equation on
the face is then `x' = x(1-x) g`, so the face is crossed from a 5% minority to a
95% majority in `5.888 / g` time units, and neutrality breaks at first order.
Under execution noise the perturbation is

    delta_m = (E[T] - 1) eta + O(eta^2) = 8.000 eta + O(eta^2)
    delta_a = 379.8 eta + O(eta^2)

so `g = eta (379.8 - 8L) + O(eta^2)`. The coefficient of `delta_m` is exact and
interpretable: a copier mirrors each of its partner's trembles exactly once, in
each of the `E[T] - 1` rounds after the first. Consequences:

* the crossing time is 15.5 time units at `eta = 1e-3` and 1.55 at `eta = 1e-2`;
* conditional safety is favoured at every `L < 47.5`, which covers the whole
  policy-relevant range;
* in a finite population, selection beats drift once `beta Z g > 1`, which at
  `beta = 0.05, Z = 100, L = 0` means `eta > 5.3 x 10^-4`.

So neutrality is a knife-edge and we now present it as one. We think this
strengthens rather than weakens the paper: the direction of the induced drift is
towards the vertex that is cheap to protect, so §3.3 is a worst case.

### Q2. Noisy proxies of m; misattribution, lagged and partial observability

New §3.9. The measurement channel is the affine family
`m^(i,j) = alpha m(i,j) + q m(j,i) + c + eps`. Proposition 20 separates the
harmless terms from the one that is not, as summarised at the top of this letter.
Table 8 and Figure 10A-B give the numbers.

On lag specifically, which the question also raises: a principal who settles on
an incident window that closed `tau` time units ago charges on the composition as
it was. Every rest point of the undelayed flow is a rest point of the delayed
one, because a constant history equals the current state, so *no threshold in the
paper moves under lag*. What lag does is reallocate basins, by up to about twenty
percentage points in our sweep, and in a direction that depends on where in the
window the liability sits (at `L = 6` the unsafe basin grows from 0.58 to 0.79 as
`tau` goes from 0 to 20; at `L = 10` it shrinks from 0.54 to 0.29). We report
this as a paragraph rather than a theorem because the invariance is the content
and the reallocation is a numerical observation.

### Q3. Robustness of the valley under networked interactions; does reciprocity expand or shrink the window?

It shrinks it, entirely from above, and closes it at `r = 0.354`. See the second
item at the top of this letter, the new *Assortative matching* paragraph in §3.8,
and Figure 10C-D. We also state what assortment does *not* answer: it is the
mean-field idealisation of structure and does not represent the local invasion
geometry of a particular graph, on which clustered aggressors can persist in
regions an assorted calculation cannot see.

The policy reading we draw is worth flagging because it was not obvious to us
before doing the calculation: structure and liability are substitutes with very
different shapes, so interoperability mandates, which lower `r`, make the choice
of liability level *more* consequential rather than less.

### Q4. Probe protocols for LLM-based agents; sensitivity to probe design and execution error

Both halves are now in the paper. The sensitivity to execution error was already
reported as margins (0.539 at `eta = 0`, then 0.449, 0.349, 0.237 at 0.02, 0.05,
0.10); we have added the translation into evaluation cost, since that is the form
in which the recommendation can be acted on: `n >= 7` episodes against `n >= 111`
for the solo probe at equal confidence, with the gap widening rather than
narrowing as execution gets noisier.

The protocol itself is now stated explicitly in §4 rather than left implicit:
run the candidate against a scripted counterpart that opens safe and thereafter
mirrors the candidate's previous action; score only the rounds not preceded by an
unsafe action of the counterpart; admit on that score rather than on behaviour
against a uniformly safe environment. We note the practical property that makes
it deployable -- the scripted counterpart needs no capability of its own, so the
evaluation does not require a second frontier system to play the aggressor -- and
we repeat the warning that the probe must not be hostile, since the design one
wants to admit is the design that fights back.

### Q5. Feasible approximations to counterparty-indexed liability; strategic manipulation of counterparties

The three approximations were given in the previous round (shape the schedule;
condition on a proxy for who moved first; certify the response rule). This round
adds two things.

First, §3.9 turns the second of them from a suggestion into a quantified
requirement, with `1/(1-q)` as the price of not doing it.

Second, we now address the manipulation question, which we had not, and we
concede the point rather than defending against it. A charge that depends on the
counterparty is inert on the *play* dynamics precisely because it does not depend
on what the charged agent does. But it does depend on whom the agent meets, and
where partners are chosen rather than drawn, that is an incentive to choose them:
a principal facing a column-constant charge has no reason to change its design
and every reason to route its agent towards counterparties with clean records.
That is a matching game our model does not contain, and it would erode the very
assortment that §3.8 shows to be protective. We therefore now describe
counterparty indexing as moving the distortion out of the design margin and into
the matching margin, and say that whether this is an improvement depends on which
margin the regulator can observe. We think this is the honest statement and it is
in §4.

### Q6. Beyond the four-strategy set: richer tit-for-tat variants, stochastic grim triggers

The previous round added a generous guard, its aggressive counterpart and a
two-round punisher; this round adds the grim trigger the question names, which
is the limit of the punisher family. Results are in W1 above. The mechanism that
appears and is new is the interaction between the length of punishment and the
error rate: longer punishment is a better guard in the noiseless game and a
worse one under noise, because the design that never forgives converts a single
tremble into permanent unsafety. At `eta = 0.05` the valley in the enlarged
pools has vanished, and for the now-familiar reason: the state liability was
protecting has stopped being safe.

We should also record what did *not* change, since it is the more useful fact
for a reader: adding designs that are absent from the {AS, CS, CAS} submatrix
leaves `L-dagger` and `L*(CAS into AS)` exactly where they were. The closed
forms are properties of a submatrix, and enlarging the pool moves basins, not
thresholds.

---

## Summary of changes

| Location | Change |
|---|---|
| Abstract | Two sentences on assortment and on measurement error |
| §1 | Limitations rewritten: four choices, each with the section that relaxes it and its headline |
| §1.1 | New paragraph *Selection on an imperfect measure* (Holmstrom 1979; Baker 1992; Holmstrom & Milgrom 1991) |
| §3 | New Table 3, *Scope of the claims*: general / exact-this-race / numerical |
| §3.7 | New Proposition 19 (rate at which twinning breaks) and its corollaries; evaluation-episode counts; grim-trigger paragraph |
| §3.8 | New paragraph *Assortative matching* with eqs. (19)-(20), Table 7; the open question in *Structured populations* is now answered |
| §3.9 | New section *What the principal can see*: Propositions 20 and 21, Table 8, lagged enforcement |
| §4 | Structured-populations paragraph rewritten; new paragraphs on attribution as a reporting requirement, on counterparty gaming, and on the probe protocol; limitations updated |
| Figures | New Figure 10 (misattribution, assortment, window edges) |
| Code | New modules `observation`, `assortment`; `grim` added to `noisy`; `scripts/run_round4.py`, `scripts/emit_round4.py`; 23 new tests (91 total, all passing) |
| References | Five added |
