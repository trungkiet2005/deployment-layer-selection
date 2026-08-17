# Referee report — round 1

**Manuscript:** *Safe designs, unsafe ecosystems: deployment-layer selection in an
evolutionary AI race*
**Venue:** Chaos, Solitons & Fractals
**Recommendation:** Major revision

---

## Summary

The manuscript studies replicator and finite-population dynamics on a four-strategy
reduced AI-race game in which the payoff driving selection differs from the payoff
that measures social outcomes, the difference being controlled by a liability
pass-through. The authors derive closed-form invasion thresholds, prove a weak
dominance relation that makes pre-deployment filtering dynamically inert, identify a
neutral safe face whose invasion barrier varies by a factor of 78, exhibit a window of
intermediate liability on which long-run harm *increases* with liability, and couple
the system to a monotone environmental state to obtain hysteresis.

The non-monotonicity result (Corollary 5) and the mixture-free invasion criterion
(Theorem 4) are genuinely interesting and, as far as I can tell, new. The numerics are
careful and the analytic branches match them. My concerns are about the framing of the
mathematical contribution, a missing literature, and several claims that outrun the
evidence.

**Strengths**
- The analytic backbone is exact: every threshold is a closed form, and the numerical
  branches sit on top of the analytic ones.
- The liability valley is a real and counterintuitive result with a clean mechanism.
- Code, tables and figures are released; the exact horizon averaging is a genuine
  improvement over the Monte Carlo evaluation of the source study.

**Weaknesses**
- A directly relevant literature — the indirect evolutionary approach — is not cited,
  and it studies exactly the separation the authors claim is unstudied.
- Several results that are presented as contributions are textbook (Lemma 2,
  Proposition 1).
- The headline thresholds are quoted in unnormalised payoff units and their
  robustness to the two most important model constants is never tested.
- The hysteresis width is an algebraic consequence of an assumed functional form.

---

## Major comments

**M1. The indirect evolutionary approach is missing, and it is the closest prior work.**
The paper's opening claim is that evolutionary game theory identifies the payoff
earned with the payoff that governs replication, and that separating them is
unstudied. That is not accurate. The indirect evolutionary approach (Güth and Yaari
1992; Güth 1995; Dekel, Ely and Yilankaya, *Rev. Econ. Stud.* 2007; Alger and Weibull,
*Econometrica* 2013) is built on precisely this separation: agents behave according to
subjective preferences while selection operates on material payoffs. Heifetz, Shannon
and Spiegel (*J. Econ. Theory* 2007) show that payoff distortions of essentially any
family are beneficial and survive payoff-monotone selection — which is the same object
as the authors' wedge, studied from the other side.

The paper's construction is in fact the *mirror image* of that literature and is more
interesting for the contrast, but it must be stated. As written, the omission reads as
unfamiliarity with the field and would by itself justify rejection at a game-theory
venue. Add the literature, and state the differentiation precisely: there the
distortion is endogenous and selection is on the socially correct functional; here the
distortion is an exogenous policy parameter and selection is on the distorted one.

**M2. Separate the textbook from the new.** Lemma 2 (invariance of replicator orbits
under column-constant perturbation) is standard and appears in Hofbauer and Sigmund.
Proposition 1 (reduction to $L=\lambda h$) is a one-line substitution. Presenting them
as contributions inflates the apparent novelty and will irritate readers who know the
material. State them as recalled facts and let Theorems 3, 4 and 6 carry the paper.

Conversely, Theorem 4 is undersold. The statement that the invasion fitness of a third
strategy at an interior two-strategy rest point has a mixture-independent sign is not
specific to this game: it holds whenever the entrant and one resident are payoff twins
against that resident. State it as a general lemma about symmetric matrix games and
then apply it. That would give the paper a result of independent interest, which is
what a methods-oriented venue is looking for.

**M3. The headline numbers are not dimensionless and their robustness is untested.**
$L^{*}_{\CAS\to\AS}=42.765$ is quoted in "payoff units per unsafe action", which is
meaningless to a reader who does not know that the prize is $B=100$ and the stage
payoffs are of order 1. Report $L/B$ throughout, or at minimum alongside.

More seriously, the entire threshold structure is driven by the winner-take-all prize.
The paper never varies $B$, and varies $p_r^{\max}$ only in an appendix remark without
recomputing any threshold. A reader cannot tell whether the liability valley is a
robust feature or an artefact of $B=100$ with $\mathbb{E}[T]=9$. Provide:
(i) the thresholds as functions of $B$ and $p_r^{\max}$;
(ii) a two-parameter diagram showing where the bistability window exists and how wide
it is. If the window closes for some $(B,p_r^{\max})$, say so — that is informative,
not damaging.

**M4. The hysteresis width is assumed, not discovered.** The authors posit
$L_{\mathrm{eff}}=L(1-\theta z)$ and then prove that recovery occurs at
$L^{*}/(1-\theta)$. That is an algebraic identity, and a reader will feel that
Theorem 7 is a restatement of the modelling choice. Two things would fix this.
First, be explicit that the non-trivial ingredient is $U\equiv 0$ *exactly* on the
protected branch (Proposition 3), which is what freezes $z$ and makes the loss
threshold independent of $\varepsilon$ and of the erosion form. Second, show that the
phenomenon survives a different erosion channel — for instance
$L_{\mathrm{eff}}=L/(1+\kappa z)$ — and report the corresponding width. Without a
second channel this section reads as a parametrisation exercise.

**M5. The abstract overclaims relative to Section 6.** The abstract states that raising
$L$ across the lower edge lifts the unsafe frequency "from 0 to 0.32". Section 6 then
explains that in a finite population the discontinuity becomes a steep but finite rise
and the valley is an escape-time phenomenon. The abstract must carry that
qualification, and the paper should quantify it: report the stationary weight of the
unsafe attractor, or the mean escape time, as a function of $Z$ and $\beta$. A claim
about bistability that dissolves under any noise is a claim about time scales, and the
time scales are not reported anywhere.

**M6. Numerical methods are not documented in the paper.** The basin averages depend on
the number of initial conditions, the sampling distribution, the integration horizon
and the seed; none of these appear in the text. Figure 5 relies on a "matched start
measure" with $\AU$ seeded at 5%, and the sensitivity of the conclusion to that 5% is
not reported. Add a short numerical-methods subsection and a sensitivity check.

**M7. Well-mixed, two-player, four fixed designs.** For this journal, the absence of any
structured-population or $N$-player consideration is a gap. I do not require new
results, but the discussion should say which of the four mechanisms are expected to
survive network reciprocity and which are not, with reasons.

---

## Minor comments

1. The introduction announces "The five results are" while the abstract says "Four
   consequences follow". Reconcile.
2. Figure 2 mixes parameterisations: panel C is labelled by $L$, panel D by
   $(1-\lambda)h$. Use one throughout, or state the correspondence in the caption.
3. Figure 5B: the $\AS$ and $\CS$ bars are zero and therefore invisible; a reader may
   think data are missing. Annotate them.
4. Author block, affiliations, competing-interest statement, CRediT roles and funding
   are absent. Elsevier also requires a Highlights list of three to five items of at
   most 85 characters.
5. "more than two orders of magnitude" — the range $0.116$ to $42.765$ is a factor of
   368, i.e. 2.5 orders. Either say "a factor of 368" or "two and a half orders".
6. Theorem 5 quotes $\delta a_{\CS}=2.631$ and $\delta m_{\CS}=4.778$ without saying
   these are $a(\CAS,\CS)-a(\CS,\CS)$ and $m(\CAS,\CS)$. Define them in the statement.
7. The claim that a liability rule "assessed on the counterparty's behaviour rather
   than one's own would not deform the dynamics at all" needs one sentence of proof or
   an explicit forward reference to Lemma 2; as written it is asserted.
8. Section 8 says the ratchet channel is "assumed rather than derived" — good — but the
   same honesty should appear in the abstract's description of the hysteresis result.

---

## Questions for the authors

1. Does the bistability window persist when the prize $B$ is comparable to the summed
   stage payoffs, i.e. when the race is not winner-take-all?
2. What is the mean first passage time out of the unsafe attractor inside the valley,
   at the $Z$ and $\beta$ you report?
3. Is Theorem 4 a special case of a general statement about symmetric matrix games?
4. How does the conclusion of Corollary 3 depend on the 5% seeding of $\AU$?
