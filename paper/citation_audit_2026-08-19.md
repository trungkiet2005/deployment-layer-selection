# Citation audit -- deployment-layer-selection (2026-08-19)

Toan bo 81 refs goc da duoc xac minh ton tai qua Crossref/arXiv/OpenAlex (khong co citation ao).

## Da sua trong refs.bib

1. `terrucha2024committing` (LOI NANG): author list sai -- dung la Terrucha, Fernandez Domingos, **Simoens, Pieter**, Lenaerts (4 tac gia). Ban cu co 'Simao, Manuel' (khong ton tai) va them Santos (khong phai tac gia).
2. `heifetz2007maximize` (LOI NANG): DOI 10.1016/j.jet.2005.09.008 tro sang paper khac (Koulovatianos & Mirman). Da sua thanh 10.1016/j.jet.2005.05.013.
3. `domingos2022delegation`: Grujic -> Gruji{'c} (thieu dau).
4. `shavell1982insurance`: note JSTOR 3003435 sai (la paper cua Nakao); thay bang doi = 10.2307/3003434.
5. `kapoor2024societal`: title chinh thuc PMLR co prefix 'Position: ...'; bo sung pages 23082--23104.

## Wording da chinh trong main.tex (claim khong khop paper duoc cite)

- bengio2024managing: paper Science 2024 khong noi ve selection pressure -> tach cau, cite cho 'competitive pressure'.
- loury1979market: bo 'reward speed over quality' (model Loury khong co chieu quality); giu rent dissipation.
- dalbo2018determinants: 'dominant behavioural regularity' -> 'dominant form of cooperative play'.
- tarnita2009strategy: bo rang buoc sigma>=1 (Tarnita cho phep sigma<1, spite); them 'large well-mixed'.
- ohtsuki2006simple/santos2006structured: 'conditionally cooperative strategies' -> 'cooperative strategies' (hai paper nay la unconditional C vs D).
- weitz/tilman: 'renewable' -> 'reversible/moves in both directions' (Tilman 2020 co ca nhanh decay).

## 16 refs moi da them (deu da verify DOI/arXiv truc tiep)

han2019bidding, han2021mediating, han2022voluntary, bova2024vigilant, lacroix2022tragedy, naude2020race, shavell1986judgment, weil2024tort, hacker2023liability, lior2022insuring, kolt2025governing, chan2024visibility, chan2024ids, nowak1992tit, herrmann2008antisocial, hauert2019asymmetric.

## Luot 2 (cung ngay): 17 goi y medium/low duoi day DA DUOC THEM vao paper

Tat ca 17 da duoc re-verify truc tiep (Crossref / Semantic Scholar / arXiv abs page / URL check) truoc khi them. Bib hien co 114 entries, khop 1-1 voi cites, compile sach (0 warning BibTeX, 0 undefined citation).

### [MEDIUM] Trust AI Regulation? Discerning users are vital to build trust and effective AI regulation (2026)
- Zainab Alalawi, Paolo Bova, Theodor Cimpeanu, Alessandro Di Stefano, Manh Hong Duong, Elias Fernandez Domingos, The Anh Han, Marcus Krellner, Ndidi Bianca Ogbo, Simon T. Powers, Filippo Zimmaro -- Applied Mathematics and Computation 508: 129627 (also arXiv:2403.09510) -- `10.1016/j.amc.2025.129627`
- Vi tri goi y: Related work / Regulation and trust in evolutionary AI-race models, and optionally in the Discussion of the retaliation mechanism behind the liability valley
- Ly do: The most recent EGT model from this group coupling developers, regulators, and users; its mechanism (conditionally trusting users disciplining developers) is the closest analogue to the paper's conditional-safe strategies whose retaliation liability taxes, so a reviewer would expect the retaliation channel to be related to it.
```bibtex
@article{alalawi-2026-trust,
  author  = {Alalawi, Zainab and Bova, Paolo and Cimpeanu, Theodor and Di Stefano, Alessandro and Duong, Manh Hong and Fern{\'a}ndez Domingos, Elias and Han, The Anh and Krellner, Marcus and Ogbo, Ndidi Bianca and Powers, Simon T. and Zimmaro, Filippo},
  title   = {Trust {AI} regulation? {D}iscerning users are vital to build trust and effective {AI} regulation},
  journal = {Applied Mathematics and Computation},
  volume  = {508},
  pages   = {129627},
  year    = {2026},
  doi     = {10.1016/j.amc.2025.129627}
}
```

### [MEDIUM] Emergent social conventions and collective bias in LLM populations (2025)
- Ariel Flint Ashery, Luca Maria Aiello, Andrea Baronchelli -- Science Advances 11(20): eadu9368 -- `10.1126/sciadv.adu9368`
- Vi tri goi y: Introduction, when arguing that ecosystem-level outcomes differ from individual design properties (or the Discussion paragraph on deployed LLM agent ecosystems)
- Ly do: High-profile evidence that populations of interacting LLM agents develop collective properties (conventions, biases) absent in any individual agent; it is the strongest published empirical support for the safe-designs-unsafe-ecosystems thesis that individual-level safety does not compose at the population level.
```bibtex
@article{ashery-2025-emergent,
  author  = {Flint Ashery, Ariel and Aiello, Luca Maria and Baronchelli, Andrea},
  title   = {Emergent social conventions and collective bias in {LLM} populations},
  journal = {Science Advances},
  volume  = {11},
  number  = {20},
  pages   = {eadu9368},
  year    = {2025},
  doi     = {10.1126/sciadv.adu9368}
}
```

### [MEDIUM] When Does Regulation by Insurance Work? The Case of Frontier AI (2025)
- Cristian Trout -- arXiv preprint (December 2025) -- `arXiv:2512.06597`
- Vi tri goi y: Discussion, deductible-and-cap paragraph (main.tex ~lines 2080-2088), together with lior2022insuring.
- Ly do: The most recent focused analysis of when regulation-by-insurance actually works for frontier AI (moral hazard, correlated and catastrophic tails, monitoring by insurers). A reviewer scanning the 2024-2026 AI-insurance-as-governance wave will expect the paper's deductible-and-cap proposal to engage with it; it also sharpens the conditions under which the paper's insurance-shaped charge is implementable by private markets versus a regulator.
```bibtex
@misc{trout2025insurance,
  author = {Trout, Cristian},
  title  = {When Does Regulation by Insurance Work? {The} Case of Frontier {AI}},
  year   = {2025},
  eprint = {2512.06597},
  archivePrefix = {arXiv},
  primaryClass  = {cs.CY}
}
```

### [MEDIUM] Cultural Evolution of Cooperation among LLM Agents (2024)
- Aron Vallinder, Edward Hughes -- arXiv preprint arXiv:2412.10270 (extended abstract in Proc. AAMAS 2025, pp. 2771-2773, DOI 10.65109/jnmb7739) -- `arXiv:2412.10270`
- Vi tri goi y: Introduction or Discussion, in the paragraph on selection pressure acting on populations of deployed AI agents, next to hendrycks2023natural
- Ly do: The first systematic study of selection/cultural-evolutionary dynamics operating on populations of actual LLM agents across generations; it provides empirical grounding for the paper's core premise that deployed AI agent designs are subject to population-level selection, updating hendrycks2023natural with concrete evidence.
```bibtex
@misc{vallinder-2024-cultural,
  author        = {Vallinder, Aron and Hughes, Edward},
  title         = {Cultural Evolution of Cooperation among {LLM} Agents},
  year          = {2024},
  eprint        = {2412.10270},
  archivePrefix = {arXiv},
  primaryClass  = {cs.MA},
  note          = {Extended abstract in Proc.\ AAMAS 2025, pp.\ 2771--2773},
  doi           = {10.48550/arXiv.2412.10270}
}
```

### [MEDIUM] An Argument for Hybrid AI Incident Reporting (2024)
- Ren Bin Lee Dixon, Heather Frase -- Center for Security and Emerging Technology (CSET), Georgetown University, Issue Brief, March 2024 -- `10.51593/20230046`
- Vi tri goi y: Discussion, incident-reporting sentence citing mcgregor2021incident and the AI Act serious-incident duties (main.tex ~lines 2115-2118).
- Ly do: The main policy design study of AI incident-reporting regimes (mandatory, voluntary, citizen reporting and what fields reports must standardise). The paper's ask that incident records carry initiator attribution is a design requirement of exactly the kind this brief catalogues; it upgrades the incident-reporting discussion beyond the already-cited McGregor 2021 database paper.
```bibtex
@techreport{dixon2024hybrid,
  author      = {Lee Dixon, Ren Bin and Frase, Heather},
  title       = {An Argument for Hybrid {AI} Incident Reporting},
  institution = {Center for Security and Emerging Technology, Georgetown University},
  type        = {Issue Brief},
  month       = {March},
  year        = {2024},
  doi         = {10.51593/20230046}
}
```

### [MEDIUM] Practices for Governing Agentic AI Systems (2023)
- Yonadav Shavit, Sandhini Agarwal, Miles Brundage, et al. (OpenAI) -- OpenAI white paper -- `https://cdn.openai.com/papers/practices-for-governing-agentic-ai-systems.pdf`
- Vi tri goi y: Discussion, either the certification paragraph (~line 2089, with cihon2021certification) or the incident-report/attribution paragraph (~lines 2105-2118).
- Ly do: The industry agenda-setter for agentic-AI governance: proposes deployer-side practices including unique agent identifiers, action logging, and incident handling. Cited across the whole 2024-2026 agent-governance literature; it connects the paper's certification-of-response-rules and attribution asks to practices frontier labs have already endorsed.
```bibtex
@techreport{shavit2023practices,
  author      = {Shavit, Yonadav and Agarwal, Sandhini and Brundage, Miles and others},
  title       = {Practices for Governing Agentic {AI} Systems},
  institution = {OpenAI},
  year        = {2023},
  url         = {https://cdn.openai.com/papers/practices-for-governing-agentic-ai-systems.pdf}
}
```

### [MEDIUM] Cooperative AI: machines must learn to find common ground (2021)
- Allan Dafoe, Yoram Bachrach, Gillian Hadfield, Eric Horvitz, Kate Larson, Thore Graepel -- Nature 593(7857): 33-36 -- `10.1038/d41586-021-01170-0`
- Vi tri goi y: Introduction, first motivation paragraph, next to bengio2024managing and hendrycks2023natural
- Ly do: The high-visibility Nature comment that made the cooperative-AI case to a general scientific audience; papers in this literature (including the Han group's) routinely cite it next to bengio2024managing as headline motivation, and it explicitly argues AI safety is a property of interacting systems rather than single agents, i.e. the paper's title thesis.
```bibtex
@article{dafoe-2021-cooperative,
  author  = {Dafoe, Allan and Bachrach, Yoram and Hadfield, Gillian and Horvitz, Eric and Larson, Kate and Graepel, Thore},
  title   = {Cooperative {AI}: machines must learn to find common ground},
  journal = {Nature},
  volume  = {593},
  number  = {7857},
  pages   = {33--36},
  year    = {2021},
  doi     = {10.1038/d41586-021-01170-0}
}
```

### [MEDIUM] Open Problems in Cooperative AI (2020)
- Allan Dafoe, Edward Hughes, Yoram Bachrach, Tantum Collins, Kevin R. McKee, Joel Z. Leibo, Kate Larson, Thore Graepel -- arXiv preprint arXiv:2012.08630 -- `arXiv:2012.08630`
- Vi tri goi y: Introduction, in the paragraph framing multi-agent AI risk and cooperative AI alongside hammond2025multiagent
- Ly do: The foundational research-agenda paper of the Cooperative AI field; the paper already cites its successor report (hammond2025multiagent) and cooperation-framing pieces (askell2019cooperation), so reviewers will notice the original agenda paper is missing from the multi-agent safety framing.
```bibtex
@misc{dafoe-2020-open,
  author        = {Dafoe, Allan and Hughes, Edward and Bachrach, Yoram and Collins, Tantum and McKee, Kevin R. and Leibo, Joel Z. and Larson, Kate and Graepel, Thore},
  title         = {Open Problems in Cooperative {AI}},
  year          = {2020},
  eprint        = {2012.08630},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  doi           = {10.48550/arXiv.2012.08630}
}
```

### [MEDIUM] Evolutionary Models of Preference Formation (2019)
- Ingela Alger and Jörgen W. Weibull -- Annual Review of Economics 11: 329-354 -- `10.1146/annurev-economics-080218-030255`
- Vi tri goi y: Introduction, the indirect-evolutionary-approach sentence (main.tex line ~178, appended to the guth1992/guth1995/dekel2007/alger2013 cluster).
- Ly do: The introduction positions the selection wedge as the mirror image of the indirect evolutionary approach, citing four primary papers (Güth-Yaari 1992, Güth 1995, Dekel et al 2007, Alger-Weibull 2013) but no survey. This Annual Review piece is the standard umbrella cite for that literature; adding it both signals command of the field and protects the 'the separation itself is not new' claim against a reviewer listing further primary papers.
```bibtex
@article{alger2019preference,
  author  = {Alger, Ingela and Weibull, J{\"o}rgen W.},
  title   = {Evolutionary models of preference formation},
  journal = {Annual Review of Economics},
  volume  = {11},
  pages   = {329--354},
  year    = {2019},
  doi     = {10.1146/annurev-economics-080218-030255}
}
```

### [MEDIUM] Partners and rivals in direct reciprocity (2018)
- Christian Hilbe, Krishnendu Chatterjee and Martin A. Nowak -- Nature Human Behaviour 2(7): 469-477 -- `10.1038/s41562-018-0320-9`
- Vi tri goi y: Section 'Execution noise and richer designs', opening paragraph (line ~1332, where designs become stochastic finite-state machines and the pool is enlarged along the punishment-severity axis).
- Ly do: Section 'Execution noise and richer designs' promotes the design pool to stochastic finite-state machines and studies which reciprocation rules survive noise; the partners-versus-rivals framework is the modern canonical treatment of exactly this design space (stochastic memory-one strategies under errors), and the paper's severity-of-punishment axis maps onto its partner/rival distinction. Reviewers current on direct reciprocity will expect a post-2012 cite here.
```bibtex
@article{hilbe2018partners,
  author  = {Hilbe, Christian and Chatterjee, Krishnendu and Nowak, Martin A.},
  title   = {Partners and rivals in direct reciprocity},
  journal = {Nature Human Behaviour},
  volume  = {2},
  pages   = {469--477},
  year    = {2018},
  doi     = {10.1038/s41562-018-0320-9}
}
```

### [MEDIUM] Winners don't punish (2008)
- Anna Dreber, David G. Rand, Drew Fudenberg and Martin A. Nowak -- Nature 452(7185): 348-351 -- `10.1038/nature06723`
- Vi tri goi y: Section 'Execution noise and richer designs', paragraph 'A design that never forgives' (lines ~1493-1499, the sentence on longer punishment being a worse citizen in a noisy ecosystem).
- Ly do: Shows experimentally that costly punishment lowers the payoff of the punisher and that high performers rely on tit-for-tat-like denial instead of punishment. This is the empirical twin of the paper's finding that harsher punishers (PUN2, GRIM) pay for their severity under noise, and it shares two authors with the already-cited Fudenberg-Rand-Dreber 2012, so its absence in the punishment-severity discussion is conspicuous.
```bibtex
@article{dreber2008winners,
  author  = {Dreber, Anna and Rand, David G. and Fudenberg, Drew and Nowak, Martin A.},
  title   = {Winners don't punish},
  journal = {Nature},
  volume  = {452},
  pages   = {348--351},
  year    = {2008},
  doi     = {10.1038/nature06723}
}
```

### [MEDIUM] Punishment and counter-punishment in public good games: Can we really govern ourselves? (2008)
- Nikos Nikiforakis -- Journal of Public Economics 92(1-2): 91-112 -- `10.1016/j.jpubeco.2007.04.008`
- Vi tri goi y: Related work, 'Liability' paragraph (line ~388) or Discussion paragraph 'Instruments that do not tax retaliation' (line ~2070).
- Ly do: The direct experimental result that when retaliation against punishers is possible, punishment is deterred and cooperation unravels; the paper's liability valley is the institutional version of the same mechanism (the instrument itself plays the role of the counter-punisher). Complements Herrmann et al 2008 in the second-order free-rider framing; medium rather than high because one of the two cites may suffice for some reviewers.
```bibtex
@article{nikiforakis2008counterpunishment,
  author  = {Nikiforakis, Nikos},
  title   = {Punishment and counter-punishment in public good games: {C}an we really govern ourselves?},
  journal = {Journal of Public Economics},
  volume  = {92},
  pages   = {91--112},
  year    = {2008},
  doi     = {10.1016/j.jpubeco.2007.04.008}
}
```

### [MEDIUM] Punitive Damages: An Economic Analysis (1998)
- A. Mitchell Polinsky, Steven Shavell -- Harvard Law Review, vol. 111, no. 4, pp. 869-962 -- `10.2307/1342009`
- Vi tri goi y: Section sec:observation, around the misattribution proposition (main.tex ~lines 1745-1793), and/or the Discussion sentence that misattribution costs one third of nominal liability (~line 2105).
- Ly do: The canonical rule that when injurers escape liability with some probability, damages should be multiplied by the reciprocal of the detection probability. This maps one-for-one onto the paper's attribution error q discounting effective liability (the 'misattribution subsidises the first strike' proposition) and formally grounds the claim that attribution is worth paying for -- or that lambda must be scaled up when q < 1.
```bibtex
@article{polinsky1998punitive,
  author  = {Polinsky, A. Mitchell and Shavell, Steven},
  title   = {Punitive Damages: An Economic Analysis},
  journal = {Harvard Law Review},
  volume  = {111},
  number  = {4},
  pages   = {869--962},
  year    = {1998},
  doi     = {10.2307/1342009}
}
```

### [MEDIUM] Assortment of encounters and evolution of cooperativeness (1982)
- Ilan Eshel and Luigi L. Cavalli-Sforza -- Proceedings of the National Academy of Sciences 79(4): 1331-1335 -- `10.1073/pnas.79.4.1331`
- Vi tri goi y: Section 'Non-linear liability, other dynamics, and structure', paragraph 'Assortative matching' (line ~1581, alongside grafen1979hawk and bergstrom2003algebra).
- Ly do: The assortative-matching subsection uses exactly the Eshel-Cavalli-Sforza construction (meet a copy of yourself with probability r, random partner otherwise) but cites only Grafen 1979 and Bergstrom 2003. Eshel-Cavalli-Sforza 1982 is the standard original for that specific r-mixture model and is the customary third member of this citation triple; a population-genetics-literate reviewer will notice the model is theirs.
```bibtex
@article{eshel1982assortment,
  author  = {Eshel, Ilan and Cavalli-Sforza, Luigi L.},
  title   = {Assortment of encounters and evolution of cooperativeness},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {79},
  pages   = {1331--1335},
  year    = {1982},
  doi     = {10.1073/pnas.79.4.1331}
}
```

### [LOW] Will Systems of LLM Agents Cooperate: An Investigation into a Social Dilemma (2025)
- Richard Willis, Yali Du, Joel Z. Leibo, Michael Luck -- arXiv preprint arXiv:2501.16173 -- `arXiv:2501.16173`
- Vi tri goi y: Discussion, in the paragraph connecting the abstract selection model to real LLM agent ecosystems (alternatively a footnote in the model section motivating design-level selection)
- Ly do: Applies evolutionary game dynamics (replicator-style selection) directly to strategies generated by frontier LLMs in a social dilemma, i.e. selection over agent designs rather than over human developers; it is the closest 2025 methodological cousin of the paper's deployment-layer selection setting and strengthens the claim that the modeling target is real.
```bibtex
@misc{willis-2025-cooperate,
  author        = {Willis, Richard and Du, Yali and Leibo, Joel Z. and Luck, Michael},
  title         = {Will Systems of {LLM} Agents Cooperate: An Investigation into a Social Dilemma},
  year          = {2025},
  eprint        = {2501.16173},
  archivePrefix = {arXiv},
  primaryClass  = {cs.MA},
  doi           = {10.48550/arXiv.2501.16173}
}
```

### [LOW] Am I an Algorithm or a Product? When Products Liability Should Apply to Algorithmic Decision-Makers (2019)
- Karni A. Chagal-Feferkorn -- Stanford Law & Policy Review, vol. 30, no. 1, pp. 61-114 -- `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3241200 (SSRN 3241200)`
- Vi tri goi y: Related work, law-and-economics-of-AI-liability sentence (main.tex ~line 381), as the products-liability contrast to the deployer-liability channel the model studies.
- Ly do: The standard products-liability-for-algorithms analysis, distinguishing when algorithmic systems should be treated as products (manufacturer liability) versus autonomous decision-makers. Pre-empts the likely reviewer question of why the paper places liability on deployers/principals rather than on developers under products-liability doctrine.
```bibtex
@article{chagalfeferkorn2019product,
  author  = {Chagal-Feferkorn, Karni A.},
  title   = {Am {I} an Algorithm or a Product? {When} Products Liability Should Apply to Algorithmic Decision-Makers},
  journal = {Stanford Law \& Policy Review},
  volume  = {30},
  number  = {1},
  pages   = {61--114},
  year    = {2019},
  note    = {SSRN No.\ 3241200}
}
```

### [LOW] Extrapolating Weak Selection in Evolutionary Games (2013)
- Bin Wu, Julián García, Christoph Hauert and Arne Traulsen -- PLoS Computational Biology 9(12): e1003381 -- `10.1371/journal.pcbi.1003381`
- Vi tri goi y: Section 'Non-linear liability, other dynamics, and structure', paragraph 'Structured populations' (lines ~1547-1555, where the sigma-criterion is applied for large L).
- Ly do: The structured-populations paragraph carries pairwise rankings 'exactly' through the Tarnita et al 2009 sigma-criterion, but that criterion is a weak-selection statement and the paper's liability parameter L scales payoff differences far beyond the weak-selection regime. Wu et al is the standard caveat cite showing weak-selection rankings need not extrapolate; one sentence citing it would preempt the obvious technical objection. Low priority because the paper already hedges with 'under weak selection and rare mutation'.
```bibtex
@article{wu2013extrapolating,
  author  = {Wu, Bin and Garc{\'i}a, Juli{\'a}n and Hauert, Christoph and Traulsen, Arne},
  title   = {Extrapolating weak selection in evolutionary games},
  journal = {PLoS Computational Biology},
  volume  = {9},
  pages   = {e1003381},
  year    = {2013},
  doi     = {10.1371/journal.pcbi.1003381}
}
```
