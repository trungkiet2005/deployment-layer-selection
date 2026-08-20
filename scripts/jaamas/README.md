# JAAMAS submission package

Everything in this directory is generated. Run `python scripts/build_jaamas.py`
from the repository root to rebuild it from `paper/` and `scripts/jaamas/`, then
`python build.py` here to compile.

Target venue: *Autonomous Agents and Multi-Agent Systems* (JAAMAS), Springer,
regular research paper.

## Contents

```
main.tex  refs.bib  main.bbl  main.pdf     the manuscript
sn-jnl.cls  sn-apanum.bst                  the Springer style, next to main.tex
                                           because that is where LaTeX looks
figures/Fig1.pdf ... Fig11.pdf             the figures
information_sheet.tex  .pdf                the sheet JAAMAS requires
cover_letter.tex       .pdf                the letter to the editors
build.py                                   compile and check
build/                                     .aux, .log, .out, .blg; disposable
```

| File | What it is |
|---|---|
| `main.tex` | The manuscript, single `.tex` file as Springer requires |
| `refs.bib` | 134 references (114 from the master plus 20 multi-agent-systems additions), APA-normalised |
| `figures/Fig1.pdf` ... `Fig11.pdf` | Figures, named and numbered as Springer requires |
| `sn-jnl.cls` | Springer Nature journal class, v3.1 (December 2024), unmodified |
| `sn-apanum.bst` | Springer's `sn-apacite.bst` with sorting suppressed (see below) |
| `information_sheet.tex` | The 1-2 page information sheet JAAMAS requires with every submission |
| `cover_letter.tex` | Cover letter to the editors |
| `build.py` | Compiles all three documents and runs the submission checks |

The figures sit in `figures/` here, but `main.tex` still writes
`\includegraphics{Fig7}` with no directory: the preamble sets
`\graphicspath{{figures/}{./}}`, so the same source compiles both from this
layout and from the single flat directory Editorial Manager unpacks an upload
into. Nothing has to be rewritten before submitting.

## What to upload

Editorial Manager wants the manuscript source, the figures, the information
sheet and the cover letter. Upload `main.tex`, `refs.bib`, `main.bbl`,
`sn-jnl.cls`, `sn-apanum.bst`, the eleven `figures/Fig*.pdf` files, and the
compiled `information_sheet.pdf` and `cover_letter.pdf`. Upload the figures as
plain files, not as a `figures` folder, and do not rename them. Including
`main.bbl` means the reference list survives even if the site's compiler cannot
find the `.bst`. Nothing in `build/` is uploaded.

## Before you submit

Five things in the package are deliberately left as placeholders, each marked
`TODO BEFORE SUBMISSION` in the source. They are in `scripts/jaamas/head.tex`
and `scripts/jaamas/tail.tex`, so editing them there survives a rebuild.

1. ORCIDs. The three authors, their shared affiliation and their e-mail
   addresses are in `head.tex`; ORCIDs go in through the Editorial Manager
   form, since `sn-jnl` has no ORCID field. Springer does not allow the author
   list to change after acceptance.
2. Acknowledgements, or delete the `\bmhead{Acknowledgements}` block if there
   are none (`tail.tex`).
3. Funding: the funder written in full plus the grant number, or keep the
   no-funding wording (`tail.tex`).
4. Author contributions (`tail.tex`) record equal contribution by all three.
   Springer also collects this through the submission interface.
5. The large-language-model statement (`tail.tex`). Springer requires
   generative use to be documented; AI-assisted copy editing alone does not
   need declaring. Edit it to match what was actually done, or delete it.

Also fill in the closing block of `cover_letter.tex`.

## Journal requirements this package already meets

- Abstract of 150 to 250 words with no citations, equations or undefined
  abbreviations; `build.py` counts it.
- Four to six keywords; `build.py` counts them.
- Numbered citations in square brackets with an APA-formatted reference list,
  which is what JAAMAS prints.
- DOIs given as full `https://doi.org/...` links.
- At most three levels of displayed heading.
- One `.tex` file, with the seven table files inlined and no `\input`.
- Figures named `Fig1` ... `Fig11` in order of first appearance, sized to the
  column width, and legible in greyscale.
- Declarations section with the eight headings Springer asks for.
- The information sheet answers all four questions JAAMAS requires. Papers with
  incomplete information sheets are returned without review.

## The reference style, and why it needs a patched `.bst`

JAAMAS cites by number in square brackets and prints an APA-formatted reference
list. Springer's class ties the two together and offers neither combination:
`sn-apa` gives APA entries with author-year citations, and `sn-basic,Numbered`
gives numbered citations with non-APA entries. The manuscript therefore loads
Springer's own APA machinery (`apacite` with `sn-apacite.bst`) and switches
natbib into numeric mode by hand, in a clearly commented block at the top of
`main.tex`.

`sn-apanum.bst` is `sn-apacite.bst` with its three sorting passes replaced by
comments, so entries come out in citation order, which is how JAAMAS prints
them. Nothing else in the style file is touched. If Springer's production team
prefers the unmodified style, deleting the block and the `\bibliographystyle`
line and adding `sn-apa` to the `\documentclass` options restores the stock
behaviour.

Two presentational fixes are applied to `refs.bib` by
`scripts/jaamas/normalise_bib.py`, and only there:

- arXiv preprints stored as `@article` with `journal = {arXiv preprint
  arXiv:ID}` become `@misc` with the identifier and DOI link in the note,
  because the APA style otherwise prints an empty volume and issue.
- `booktitle` fields are brace-protected, because the APA style sentence-cases
  proceedings titles and would print "proceedings of the aaai conference".

Two author lists that end in `and others` are completed from Crossref, because
APA renders `others` literally rather than as "et al.".

## Differences from `paper/`

`paper/main.tex` stays the venue-neutral master and is unchanged. The JAAMAS
version differs from it in:

- the Springer front matter, abstract, keywords and declarations;
- the reference style, and 20 added multi-agent-systems references, each
  verified twice against Crossref (`scripts/jaamas/refs_mas.bib`); nine are
  JAAMAS articles;
- six spliced passages listed in `scripts/jaamas/insertions.tex`: why this is a
  multi-agent systems problem, a Related work paragraph on the MAS literature,
  a statement of the claim and the evidence ahead of the four results, an
  incomplete-contracting sentence, a Discussion paragraph on what the results
  mean for MAS designers, and one accuracy fix;
- the inlined tables, the renamed figures, and one table column narrowed to fit
  the narrower Springer text block.

No result, figure or number changes. The one accuracy fix is in the
introduction: the master says the non-monotonicity "makes intermediate regimes
worse than none", but at zero liability the whole population is unsafe
(`results/round4.json`), so an intermediate liability is better than none, not
worse. What the valley result actually says, and what the paper says everywhere
else, is that it is worse than a *weaker* setting just below the window's lower
edge. The JAAMAS version says that instead. The same correction is worth making
in `paper/main.tex`.

## If the editors ask for a blinded or double-spaced version

Add `referee` to the `\documentclass` options for double spacing. For a blinded
version, remove the `\author`, `\affil` and `\email` lines and the repository
URL in the declarations.
