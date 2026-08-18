# Response to the reviewer

**Manuscript:** *Safe designs, unsafe ecosystems: deployment-layer selection in an
evolutionary AI race*

We thank the reviewer for a report that is unusually precise about what the paper
does and does not establish. The recommendation of acceptance after moderate
revision, and in particular the seven questions, gave us a clear programme. We have
carried out all of it. The revision adds two results sections
(§3.7 *Execution noise and richer designs*, §3.8 *Non-linear liability, other
dynamics, and structure*), one new proposition in each of §3.1 and §3.2, a
generalised hysteresis theorem, three new tables, one new figure, and eight new
references.

Two of the reviewer's questions changed a conclusion rather than confirming one, and
we flag those first because they are the substantive content of this revision:

* **The evaluation result is now constructive and sharper.** Asked what a
  multi-agent adversarial evaluation would buy (Q7), we enumerated all fifteen probe
  sets. The separating margin takes exactly two values, and the determining property
  is not adversarialness but *reciprocity*: probing against a conditionally safe
  counterpart quadruples the margin (0.132 → 0.539), while probing against a
  maximally hostile one destroys the gain, because conditional safety retaliates
  against it in 87% of rounds and is scored as unsafe. This is now
  Proposition 12, and it is a concrete implementable recommendation rather than the
  negative result the paper previously ended on.
* **Weak dominance is a property of the pool, and we now say so.** Asked about
  richer strategy sets (Q2), we found that Theorem 10 fails once the pool contains a
  two-round punisher: against it, unconditional aggression outearns conditional
  aggression by 15.48, because uninterrupted unsafe play wins the race outright
  while conditional aggression, thrown out of phase, only ties. Dominance is
  restored for L ≥ 15.48. We report this in §3.7 and revise the corresponding
  limitation. The policy reading improves: filtering is empty *unless* the surviving
  pool contains a design that punishes for longer than it is punished.

Everything below is keyed to the reviewer's numbering.

---

## Weaknesses

### W1. Sensitivity to richer conditional strategies (noisy/generous variants, forgiveness and punishment lengths, probabilistic behaviour)

New §3.7. We promote each design to a stochastic finite-state machine, add
trembling-hand execution noise η, and enlarge the pool with a generous guard that
forgives an observed unsafe action with probability 0.25, its aggressive counterpart,
and a two-round punisher. Evaluation remains exact — the joint chain over the two
internal states is propagated against the horizon law, carrying the progress
difference and unsafe count as state and the accumulated stage payoff as a first
moment — so no sampling noise enters the payoff matrix. At η = 0 the new evaluator
reproduces Tables 1–2 to 1.1 × 10⁻⁶, which is the horizon truncation.

Findings: the guard threshold L† moves by less than 12% over η ∈ [0, 0.10]; the
bistability window persists at every noise level but narrows from 10.0 to 2.6; the
valley closes at η ≥ 0.075; and the valley survives every enrichment of the pool,
with depth 0.299 (baseline), 0.344, 0.163, 0.181 and 0.084 for the four enlarged
pools at η = 0.

### W2. Well-mixed, pairwise interactions

New paragraphs *Structured populations* and *Multi-player faces* in §3.8. Two of the
four mechanisms are now carried over exactly rather than conjecturally, using the
structure coefficient of Tarnita et al. (2009):

* the safe face is neutral for **every** structure, because all four entries of π_P
  on {AS, CS} coincide and the σ-criterion reduces to an identity;
* the criterion is affine in L for each σ, giving eq. (17). Assortment substitutes
  for liability at a steep rate: protecting unconditional safety needs L > 6.14 at
  σ = 1, L > 1.56 at σ = 2, and nothing at σ ≥ 2.93; protecting conditional safety
  needs nothing at all already at σ ≥ 1.10.

For multi-player faces we give the honest generalisation of Lemma 16: the twin
hypothesis kills the s = 0 term of the invasion sum, so mixture-freeness survives as
a *sufficient* condition (a_k(s) ≥ a_i(s) for all s ≥ 1, strict somewhere) and is
necessary only for N = 2. The valley itself we cannot settle under assortment, and
we say so.

### W3. Liability modelled as linear pass-through

New paragraph *Non-linear charges* in §3.8 and Table 5. The charge becomes L·φ(m)
for any strictly increasing φ with φ(0) = 0, normalised so φ(9) = 9. Lemma 7
survives verbatim with δm → δφ, so all closed forms persist. We report five shapes.
The valley exists in all of them, and the ends of the range behave oppositely: a
convex charge widens the window from 10.0 to 42.3 (it barely charges the single
unsafe action with which CAS exploits AS), while concave and capped charges narrow
it to 4.9 and 7.1. A de minimis rule that charges nothing below two incidents never
protects unconditional safety at any liability. This also supplies the answer to Q5
below.

### W4. Hysteresis not fully detailed

Theorem 19 is restated for a *class* of erosion channels — any continuous,
non-increasing, normalised L_eff — rather than for an assumed functional form, and
the proof now makes explicit where each hypothesis is used and where ε does not
appear. Table 6 sweeps two channels, two residual fractions and a factor of twenty
in ε; the observed ratio tracks 1/ρ throughout and is unchanged by ε.

We also state the boundary of the result explicitly, which the previous version did
not: freezing of the protected branch requires U = 0 *exactly*, and under execution
noise it does not hold, so the loss threshold becomes a race between the sweep and
the ratchet. We found this the hard way — an initial sweep from a uniform start with
mutation 10⁻⁴ gave apparent ε-dependence, which turned out to be the protected branch
failing to freeze.

### W5. Alternative evolutionary dynamics

New Proposition 8 and paragraph *Other selection dynamics* in §3.8, plus
Figure 9B. See Q3.

### W6. No calibration

New paragraph *Reading the liability axis* in §4. We continue to decline a point
calibration of h, for the reason the reviewer anticipates, but we now give the axis
a reading in units of the prize, which is the one quantity a deploying firm knows:
the four thresholds are L/B = 0.0012, 0.0055, 0.043 and 0.428, and §3.6 shows the
outer one stays in [0.38, 0.61] across the whole grid. The comparative statement —
protecting unconditional safety costs about half the prize per unsafe step,
conditional safety under one per cent of it, and the dangerous range lies between
roughly four per cent and half the prize — is available without estimating h. We
also say what an honest calibration would require, and that this model does not
supply it.

### W7. Notation and typos

We could not reproduce a `πρ`/`π_P` inconsistency in the source: the manuscript uses
a single macro `\piP` throughout, and we believe the reviewer saw an artefact of PDF
text extraction of `\pi_{P}`. We have nevertheless reread the manuscript for
notation and fixed the inconsistencies we did find.

### W8. Key constants not reproduced inline

Tables 1 and 2 (task payoffs and unsafe counts) have moved from the appendix into
§2, with a sentence pointing out the two features of m that carry the results. The
appendix now contains the twelve invasion thresholds and a sentence on how they are
derived from the two tables.

### W9. Missing related work

Two new paragraphs in §1.1, with eight new references:

* *Two-level selection* — Wilson (1975), Traulsen & Nowak (2006), Okasha (2006),
  positioning the outside-the-game principal as a degenerate but sharper case: one
  selecting level, which is not the level that plays, and whose functional is a
  policy variable rather than an aggregate of the lower level.
* *Incentive design in evolutionary games* — Sigmund et al. (2010), Wang, Chen &
  Szolnoki (2019), noting that those instruments enter the players' own payoffs and
  are monotone in budget, whereas ours acts one level up and is not.

We also added Tarnita et al. (2009), Sandholm (2010), Posch et al. (1999) and
Cihon et al. (2021) where the new analyses use them.

---

## Questions

### Q1. Hysteresis: full derivation, coupling assumptions, sensitivity across coupling classes

Covered in W4. To be explicit about the three points asked: the assumption on the
coupling is now only that L_eff is continuous, non-increasing in z, strictly
increasing in L and normalised at z = 0; the derivation shows ε enters nowhere
because it scales the speed of z but not its limit; and Table 6 verifies
ε-independence over a factor of twenty and channel-independence at matched ρ. The
non-trivial ingredient is Proposition 13 (U = 0 exactly on the protected branch), not
the channel — and when that fails, so does the result.

### Q2. Sensitivity to enriched strategy sets and ε-trembles

Covered in W1. Directly to the sub-question — *do small implementation errors
qualitatively alter the valley?* — the answer is a quantitative yes with a threshold:
depth 0.299 → 0.149 → 0.089 → 0.025 → 0 at η = 0, 0.01, 0.02, 0.05, 0.075. The
mechanism is worth stating because it is not the one we expected: the window between
the two invasion thresholds never closes, but the *harm difference* between the two
attractors does, because a conditionally safe population stops being safe once it
retaliates against its own trembles (u(CS,CS) = 0.186 at η = 0.05). Liability becomes
monotone again above 7.5% error only because the state it was protecting is no longer
protected. We say this in the text rather than presenting the closure as reassurance.

A second noise finding strengthens a policy conclusion: with η > 0 the safe face
stops being neutral, and the gradient points at conditional safety for every L below
44.3 (η = 0.01) down to 26.4 (η = 0.10) — the whole policy-relevant range. The drift
argument of §3.3 is therefore a worst case, not the typical case.

### Q3. Other dynamics — best response with inertia, aspiration learning, pairwise proportional imitation

New Proposition 8 makes the cheap part rigorous and, importantly, delimits it. For
*imitative* payoff-monotone dynamics (replicator, pairwise proportional imitation,
imitation of the better) all three structural claims hold verbatim, because each is a
statement about the sign of a fitness difference. For best response, whose rest points
are the symmetric Nash equilibria, we show the interior rest point of the {AS, CAS}
face is Nash in the three-design game **iff** L ≥ L†, so the bistable window opens at
the same threshold.

We also correct an overreach we had initially written into this proposition: logit and
best response are *not* imitative, and the neutral safe face is **not** a rest set for
them — both contract it to its barycentre, because a vanishing design is replenished
at a rate that does not vanish with its frequency. Neutrality of the face is a
property of the payoffs; the drift story requires imitation. This is now stated as a
caveat and covered by a test.

Numerically (Figure 9B): valley depth 0.305 (replicator), 0.417 (logit β = 10),
0.171 (logit β = 1), 0.433 (best response), all with the edge at L†. Aspiration
dynamics, which satisfies neither hypothesis, shows a different failure mode: harm is
monotone in L but stops responding to it, settling at 0.237 for every L ≥ 4. The
instrument does not backfire; it loses traction.

### Q4. Networks and multi-party interactions; does the mixture-independence lemma extend?

Covered in W2. Short answer: neutrality of the safe face extends to arbitrary
structure exactly; the pairwise comparisons extend with a σ-dependent threshold that
we give in closed form; Lemma 13 extends to N players as a sufficient condition, and
its "if and only if" is special to N = 2; and the valley we leave open, with the
direction the mechanism predicts stated.

### Q5. Practical instruments approximating counterparty-indexed penalties

New paragraph *Instruments that do not tax retaliation* in §4, giving three
approximations in increasing order of information required:

1. **Shape the schedule instead of indexing it.** Table 5 shows a concave or capped
   schedule narrows the window to 4.9 from the linear 10.0, because saturation spares
   the retaliator (high incident count) more than the initiator (count one).
   Deductible-and-cap structures have exactly this shape, which is an argument for
   liability mediated by insurers over liability assessed per incident. We think this
   is the most useful thing this revision adds on the policy side, and it came
   directly from the reviewer's question.
2. **Condition on an observable proxy for who moved first** — an incident report
   recording the counterparty's prior action, which an interaction audit log already
   contains.
3. **Certify the response rule rather than the behaviour** (Cihon et al. 2021): a
   design certified as retaliation-only is charged column-constantly and, by Lemma 4,
   does not deform the dynamics at all.

The reframing we draw is that the obstacle is informational, not legal: incident data
does not currently record who initiated.

### Q6. Mapping real liability regimes onto the L/B axis

Covered in W6. We give the axis a reading in prize units and the comparative
statement that follows, and decline the point calibration.

### Q7. Would a minimal multi-agent adversarial evaluation change the filtering conclusion?

Yes, and the answer is sharper than "adversarial helps" — see the summary above and
new Proposition 12. The margin over all fifteen probe sets takes exactly two values,
0.132 and 0.539; it is 0.539 precisely when the probe set contains a conditional
design and does not contain an always-unsafe one. The best probe is a single
reciprocating counterpart. Two caveats are retained: the admitted pool is the neutral
safe face, so gating must be continuous rather than one-off; and the wide band
requires tolerating a design that is unsafe in 46% of rounds against an aggressor —
which is exactly the retaliation liability taxes. An evaluation rule and a liability
rule that both score retaliation as harm work against each other.

---

## Summary of changes

| Location | Change |
|---|---|
| Abstract | Robustness sentence added; hysteresis claim restated for a channel class |
| §1 | Limitations paragraph now forward-references the two robustness sections |
| §1.1 | New paragraphs on two-level selection and on incentive design |
| §2 | Tables 1–2 moved inline; numerical-methods note extended |
| §3.1 | New Proposition 8 (thresholds are properties of π_P, with its caveat) |
| §3.2 | New Proposition 12 (the probe must reciprocate) and revised discussion |
| §3.7 | New: execution noise and richer designs; Table 4 |
| §3.8 | New: non-linear charges (Table 5), other dynamics, structure, multi-player |
| §3.9 | Hysteresis theorem generalised to a channel class; Table 6; noise caveat |
| §4 | New paragraphs: reading the L-axis; instruments that do not tax retaliation; structured populations rewritten |
| §4 | Limitations expanded from four to five, with the noise threshold |
| Figures | New Figure 9 (noise, dynamics, charge shape) |
| Appendix A | Now the threshold table only, with a derivation sentence |
| Code | New modules `noisy`, `altdynamics`, `charges`, `probes`; `ratchet` generalised; `scripts/run_extensions.py`, `scripts/emit_extensions.py`; 19 new tests (68 total, all passing) |
| References | Eight added |
