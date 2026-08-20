r"""Generate the JAAMAS submission package in paper-jaamas/ from paper/.

The venue-neutral manuscript in paper/main.tex stays the master.  Everything
that is specific to Autonomous Agents and Multi-Agent Systems lives here and in
scripts/jaamas/:

  scripts/jaamas/head.tex      preamble, title page, author block
  scripts/jaamas/abstract.tex  \abstract{} and \keywords{}
  scripts/jaamas/tail.tex      acknowledgements and Springer declarations
  scripts/jaamas/insertions.tex  venue-specific prose spliced into the body
  scripts/jaamas/normalise_bib.py  APA-style fixes to refs.bib
  scripts/jaamas/build.py      the compile-and-check script, copied into the
                               package (everything in paper-jaamas/ is
                               generated, so nothing is authored there)

What the script does to the body, and why:

  1. Inlines every \input{...}.  Springer: "Please do not use \input{...} to
     include other tex files.  Submit your LaTeX manuscript as one .tex
     document."
  2. Renames the figure files to Fig1.pdf ... Fig11.pdf in order of first
     appearance and puts them in paper-jaamas/figures/.  Springer: "Name your
     figure files with 'Fig' and the figure number."  The \graphicspath in
     head.tex searches figures/ and then ./, so the manuscript also compiles
     against the flat directory Editorial Manager unpacks the upload into.
  3. Replaces the venue-neutral Declarations block with the Springer one, and
     wraps the appendices in the appendices environment the class expects.
  4. Splices in the multi-agent-systems framing passages.

Run:  python scripts/build_jaamas.py
Then: cd paper-jaamas && python build.py
"""
import os
import re
import shutil
import sys

B = chr(92)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'paper')
DST = os.path.join(ROOT, 'paper-jaamas')
FIGS = os.path.join(DST, 'figures')
FRAG = os.path.join(HERE, 'jaamas')
# Springer's class and its APA .bst.  The downloaded template package wins when
# it is present, so upgrading is one download away; the two files the build
# actually reads are also vendored under scripts/jaamas/springer-template/, both
# LPPL, so that a clean clone regenerates the package without the download.  The
# package directory sn-template-extract/ is .gitignored, which is why the
# fallback exists at all.
TPL = os.path.join(ROOT, 'sn-template-extract', 'sn-article-template')
VENDORED = os.path.join(HERE, 'jaamas', 'springer-template')
if not os.path.exists(os.path.join(TPL, 'sn-jnl.cls')):
    TPL = VENDORED
    print('template package not found; using vendored copy in %s'
          % os.path.relpath(VENDORED, ROOT))

sys.path.insert(0, FRAG)
import normalise_bib                                              # noqa: E402

LAYOUT_FIXES = [
    (r'\begin{tabular}{llp{6.6cm}}', r'\begin{tabular}{llp{5.4cm}}'),
]


def rx(pat, flags=0):
    return re.compile(pat.replace('@', B), flags)


def main():
    os.makedirs(DST, exist_ok=True)

    # ------------------------------------------------------------ class + bst
    shutil.copy(os.path.join(TPL, 'sn-jnl.cls'), DST)

    # sn-apanum.bst is Springer's own sn-apacite.bst with its three sorting
    # passes suppressed, so the numbered list comes out in citation order, and
    # with a widest-label argument so natbib can size the numeric labels.
    bst = open(os.path.join(TPL, 'bst', 'sn-apacite.bst'),
               encoding='utf8', errors='replace').read()
    lines = bst.split('\n')
    out, removed, relabelled = [], 0, 0
    driver = len(lines) - 60
    for i, line in enumerate(lines):
        if line.strip() == 'SORT' and i > driver:
            out.append('% SORT suppressed: numbered list in citation order')
            removed += 1
        elif 'begin{thebibliography}{}' in line:
            out.append(line.replace('{thebibliography}{}', '{thebibliography}{999}'))
            relabelled += 1
        else:
            out.append(line)
    assert removed == 3, 'expected 3 SORT passes, removed %d' % removed
    assert relabelled == 1, 'thebibliography label width not patched'
    open(os.path.join(DST, 'sn-apanum.bst'), 'w', encoding='utf8').write('\n'.join(out))

    # ---------------------------------------------------------------- sources
    src = open(os.path.join(SRC, 'main.tex'), encoding='utf8').read()
    body = src[src.index(B + 'section{Introduction}'):src.index(B + 'end{document}')]

    # ------------------------------------------------- 1. inline \input files
    def inline(m):
        name = m.group(1)
        txt = open(os.path.join(SRC, name + '.tex'), encoding='utf8').read().rstrip('\n')
        return ('%%%% ---- begin inlined %s.tex ----\n%s\n'
                '%%%% ---- end inlined %s.tex ----' % (name, txt, name))

    body, n_input = rx(r'@@input\{([^}]+)\}').subn(inline, body)

    # ----------------------------------------- 2. rename figures to FigN.pdf
    figpat = rx(r'@@includegraphics(\[[^\]]*\])?\{figures/([A-Za-z0-9_]+)@.pdf\}')
    order = []
    for m in figpat.finditer(body):
        if m.group(2) not in order:
            order.append(m.group(2))
    figmap = {stem: 'Fig%d' % i for i, stem in enumerate(order, start=1)}
    os.makedirs(FIGS, exist_ok=True)
    for stale in os.listdir(FIGS):                    # drop figures no longer cited
        if stale not in {new + '.pdf' for new in figmap.values()}:
            os.remove(os.path.join(FIGS, stale))
    for stem, new in figmap.items():
        shutil.copy(os.path.join(SRC, 'figures', stem + '.pdf'),
                    os.path.join(FIGS, new + '.pdf'))
    body, n_fig = figpat.subn(
        lambda m: B + 'includegraphics' + (m.group(1) or '') + '{' + figmap[m.group(2)] + '}',
        body)

    # -------------------------------- 3. split off the venue-neutral tail
    decl_start = body.index(B + 'section*{Declarations}')
    appendix_at = body.index(B + 'appendix', decl_start)
    bib_at = body.index(B + 'bibliographystyle{unsrtnat}')
    main_body = body[:decl_start].rstrip()
    appendices = body[appendix_at:bib_at].replace(B + 'appendix', '', 1).strip()

    main_body = rx(r'^%={10,}\n', re.M).sub('', main_body)
    appendices = rx(r'^%={10,}\n', re.M).sub('', appendices)

    # sn-jnl's text block is 31pc wide against the master's 16.5cm, so the one
    # fixed-width table column has to come in by the difference.
    for old, new in LAYOUT_FIXES:
        assert old in main_body, 'layout fix target missing: %r' % old
        main_body = main_body.replace(old, new)

    # ------------------------------ 4. splice in the venue-specific passages
    n_splice = 0
    ins_path = os.path.join(FRAG, 'insertions.tex')
    if os.path.exists(ins_path):
        blocks = parse_insertions(open(ins_path, encoding='utf8').read())
        for anchor, mode, text in blocks:
            hits = main_body.count(anchor)
            assert hits == 1, ('insertion anchor occurs %d times, expected 1: %r'
                               % (hits, anchor[:70]))
            if mode == 'after':
                main_body = main_body.replace(anchor, anchor + '\n\n' + text.strip(), 1)
            elif mode == 'before':
                main_body = main_body.replace(anchor, text.strip() + '\n\n' + anchor, 1)
            else:                                                    # replace
                main_body = main_body.replace(anchor, text.strip(), 1)
            n_splice += 1

    # ------------------------------------------------------------ 5. assemble
    head = open(os.path.join(FRAG, 'head.tex'), encoding='utf8').read().rstrip()
    abstract = open(os.path.join(FRAG, 'abstract.tex'), encoding='utf8').read().rstrip()
    tail = open(os.path.join(FRAG, 'tail.tex'), encoding='utf8').read().rstrip()

    doc = '\n'.join([
        head, '', abstract, '', B + 'maketitle', '',
        main_body, '', tail, '',
        # sn-jnl restarts the table and figure counters in the appendices, so
        # Table A1 and Table 1 both ask hyperref for the anchor "table.1" and
        # pdflatex warns "destination with the same identifier"; the second
        # anchor is dropped and one of the two links then goes to the wrong
        # float.  Giving the appendix floats their own hyperref counter costs
        # nothing and is invisible in the typeset output.
        B + 'begin{appendices}', '',
        B + 'renewcommand{' + B + 'theHtable}{app.' + B + 'thetable}',
        B + 'renewcommand{' + B + 'theHfigure}{app.' + B + 'thefigure}', '',
        appendices, '', B + 'end{appendices}', '',
        B + 'bibliography{refs}', '', B + 'end{document}', ''])
    open(os.path.join(DST, 'main.tex'), 'w', encoding='utf8').write(doc)

    # ---------------------------------------------------------------- 6. bib
    raw = open(os.path.join(SRC, 'refs.bib'), encoding='utf8').read()
    newbib, n_arxiv, n_book = normalise_bib.normalise(raw)
    assert raw.count('\n@') == newbib.count('\n@'), 'bib entry count changed'
    mas_raw = open(os.path.join(FRAG, 'refs_mas.bib'), encoding='utf8').read()
    n_mas = mas_raw.count('\n@')
    for key in re.findall(r'@[a-z]+\{([^,]+),', mas_raw):
        assert '{' + key + ',' not in raw, 'MAS key already in refs.bib: ' + key
    # The venue-specific entries need the same APA normalisation as the master
    # bib.  Appending them raw left three proceedings titles to be
    # sentence-cased by the style, so AAMAS printed as "autonomous agents and
    # multiagent systems" in the reference list.
    mas, mas_arxiv, mas_book = normalise_bib.normalise(mas_raw)
    assert mas_raw.count('\n@') == mas.count('\n@'), 'MAS bib entry count changed'
    n_arxiv += mas_arxiv
    n_book += mas_book
    open(os.path.join(DST, 'refs.bib'), 'w', encoding='utf8').write(
        newbib.rstrip() + '\n\n' + mas)

    # ------------------------------------------- 7. accompanying documents
    n_doc = 0
    for name in ('information_sheet.tex', 'cover_letter.tex', 'README.md',
                 'build.py'):
        p = os.path.join(FRAG, name)
        if os.path.exists(p):
            shutil.copy(p, DST)
            n_doc += 1

    print('inlined table files    : %d' % n_input)
    print('figures renamed        : %d' % n_fig)
    for stem, new in figmap.items():
        print('    %-24s -> figures/%s.pdf' % (stem + '.pdf', new))
    print('venue passages spliced : %d' % n_splice)
    print('accompanying documents : %d' % n_doc)
    print('bib entries            : %d master + %d multi-agent-systems '
          '(%d arXiv reshaped, %d booktitles protected)'
          % (raw.count('\n@') + 1, n_mas, n_arxiv, n_book))
    print('main.tex               : %d bytes' % os.path.getsize(os.path.join(DST, 'main.tex')))


def parse_insertions(text):
    """Parse scripts/jaamas/insertions.tex into (anchor, mode, payload) triples.

    Format, repeated:

        %%>> AFTER: <verbatim anchor string from paper/main.tex>
        ... LaTeX to splice ...
        %%<< END
    """
    blocks = []
    pat = re.compile(r'^%%>>\s+(AFTER|BEFORE|REPLACE):\s*(.*?)\s*$', re.M)
    marks = list(pat.finditer(text))
    for i, m in enumerate(marks):
        start = m.end()
        stop = text.index('%%<< END', start)
        payload = text[start:stop]
        blocks.append((m.group(2), m.group(1).lower(), payload))
    return blocks


if __name__ == '__main__':
    main()
