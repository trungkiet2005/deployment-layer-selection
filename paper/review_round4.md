# Referee report -- round 4

**Estimated score:** 6.7/10 (calibrated to the ICLR scale).
**Recommendation:** accept, with encouragement to expand robustness analyses
(especially under network structure and noisy observables) and to discuss
practical design and measurement of the evaluation probes and liability
proxies.

## Summary

This paper formalizes a selection-layer wedge between the payoff an AI agent
earns in an interaction (task payoff) and the payoff that governs replication
(principal's selection functional), induced by partial pass-through of external
harm via liability lambda. Embedding this decoupling in a reduced four-strategy
AI race (AS, AU, CS, CAS), the authors show that all deployment dynamics
collapse to an effective liability L = lambda h and that invasion conditions are
affine in L, yielding closed-form thresholds. The main findings are that: (i)
solo pre-deployment evaluation is dynamically inert because conditional
aggression (CAS) weakly dominates unconditional aggression (AU); (ii) the "safe
face" {AS, CS} is payoff-neutral, yet the invasion barrier against CAS depends
on a drifting composition variable and decreases by a factor of 77.7; (iii)
harm is non-monotone in L due to liability taxing retaliation, creating a
bistable "liability valley"; and (iv) coupling to irreversible capability
diffusion yields hysteresis with exactly computable width. The results shift
governance focus from design-layer filtering to selection-layer instruments and
identify intermediate liability regimes that can be worse than either extreme.

## Strengths

**Technical novelty.** Introduces and formalizes the selection wedge as a
decoupling between interaction payoff and selection functional, tailored to AI
deployment with partial liability pass-through. Collapses policy dependence to
effective liability L = lambda h and proves general affine invasion thresholds;
several results (e.g. Lemma 16) extend beyond the specific race game to any
symmetric matrix game. Identifies a counterintuitive, policy-relevant "liability
valley" where intermediate liability increases long-run harm by taxing
retaliation that sustains conditional safety. Derives exact, interpretable
thresholds and closed forms (e.g. L-dagger, L*(x)), enabling transparent policy
interpretation.

**Experimental rigor.** Uses exact evaluation of deterministic strategy matchups
over the race's stochastic horizon, avoiding Monte Carlo noise in critical
differences. Combines replicator dynamics with finite-population Fermi
imitation; discusses robustness to alternative imitation rules and best
response. Provides careful numerical protocols (tolerances, basin averages,
stationary distributions), with code release claimed. Reports sensitivity to
prize/risk parameters and considers alternative liability schedules and richer
strategy sets in later sections.

**Clarity.** Clear separation of interaction vs selection layers with concise
definitions of task, principal, and social functionals and the wedge.
Statements, lemmas, and corollaries are precisely formulated with direct proofs;
key thresholds are computed and interpreted. Figures are well-motivated and
align with the main claims.

**Significance.** Shifts the locus of AI governance analysis from design-time
controls to selection-time incentives, with actionable insights on liability
design. Provides exact mechanisms for why solo evaluation can be ineffective and
why multi-agent reciprocating probes are necessary. The non-monotonicity and
hysteresis results articulate real policy risks from partial measures.

## Weaknesses

**Technical limitations.** Relies on a stylized, four-strategy reduced race with
two-player repeated interactions; excludes richer dynamics such as multi-agent
market/ecosystem competition, gradual capability accumulation, and learning. The
key policy parameter L is uncalibrated and aggregated; practical mapping from
real-world liability regimes to L (and measuring m) is nontrivial. Neutrality of
the safe face depends on payoff "twinning" that may be fragile with richer
action/state spaces or in the presence of learning/misattribution.

**Experimental gaps.** While robustness to imitation rules and some liability
schedules is discussed, the excerpt provides limited details on networked
populations or path-dependent institutions (beyond a stated return in later
sections). The finite-population analysis shows long survival times of unsafe
attractors but could probe a wider range of mutation rates, intensities, and
initializations. The modeling of evaluation filters as thresholds on unsafe
frequency in a safe environment is simple; real evaluations are
multi-dimensional and context-dependent.

**Clarity.** Some policy conclusions depend on sections not fully included (e.g.
non-linear schedules, additional conditional designs, other dynamics): clearer
up-front scoping of which conclusions rely on those extensions would help. The
narrative sometimes interleaves general results with numbers specific to one
parameterization; clearer separation would aid readers tracking generality vs
instance.

**Missing related work.** Could broaden connections to principal-agent models
where selection operates via imperfect observables, and to sanctioning /
second-order free rider literature with explicit institutional noise. Empirical
evidence beyond Fernandez Domingos & Han could further motivate the conditional
strategies and the retaliation-as-guard mechanism.

## Questions for authors

1. How robust is the neutral safe-face result to modest departures from exact
   payoff twinning (e.g. slight asymmetries in AS vs CS against AS due to
   stochastic execution or measurement noise)? Is there a perturbation analysis
   characterizing how quickly neutrality breaks?

2. In practice, principals observe noisy proxies of m (unsafe actions) and a;
   how does misattribution or lagged/partial observability affect the effective
   wedge and the key thresholds (L-dagger, L*(x))?

3. Could you provide more detail on the robustness of the liability valley under
   networked interactions (assortative matching or clusters), and whether
   network reciprocity expands or shrinks the bistable window?

4. The multi-agent evaluation proposal hinges on reciprocation; what specific
   probe protocols would you recommend for modern LLM-based agents, and how
   sensitive is the widened margin to probe design or small execution error
   rates?

5. Proposition 6 suggests only full pass-through achieves social dynamics; are
   there feasible, implementable approximations to the "column-constant"
   (counterparty-based) liability that would be legally/politically realistic,
   and how would strategic manipulation of counterparties affect it?

6. Can you share additional results or intuition for how the thresholds scale
   when moving beyond the reduced four-strategy set (e.g. richer tit-for-tat
   variants, stochastic grim triggers), and whether new mechanisms arise?

## Overall assessment

This paper makes a conceptually novel and technically solid contribution by
formalizing deployment-layer selection for AI agents and deriving sharp,
policy-relevant consequences. The selection wedge perspective leads to clean
analytical thresholds, an unexpected liability-induced bistability, and a
compelling diagnosis of why solo evaluation can be ineffective while
reciprocating multi-agent probes are beneficial. While the model is deliberately
stylized and the mapping from real-world instruments to the effective liability
L is abstract, the authors' analysis is careful, the mechanisms are transparent
and generalizable in part (e.g. Lemma 16), and the governance implications are
important and timely. I recommend acceptance.
