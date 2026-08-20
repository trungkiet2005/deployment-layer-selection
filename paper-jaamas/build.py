"""Compile the JAAMAS manuscript and the two accompanying documents.

    python build.py            main.tex, information_sheet.tex, cover_letter.tex
    python build.py main       only the manuscript

Runs pdflatex / bibtex / pdflatex / pdflatex and then reports the things the
journal actually checks: LaTeX errors, undefined citations and references,
abstract word count, keyword count and page count.

Every intermediate file (.aux, .log, .out, .blg) is written to build/ so that
the package directory holds only what gets uploaded.  The four deliverables,
main.pdf, main.bbl and the two accompanying PDFs, are moved back up beside the
sources when the run finishes.

This file is generated: the master is scripts/jaamas/build.py, and editing the
copy in paper-jaamas/ does not survive a rebuild.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build')

# What gets uploaded: kept beside the sources rather than buried in build/.
DELIVERABLES = {'main': ['main.pdf', 'main.bbl'],
                'information_sheet': ['information_sheet.pdf'],
                'cover_letter': ['cover_letter.pdf']}


def run(cmd):
    return subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                          encoding='utf8', errors='replace')


def latex(stem, with_bib=True):
    tex = ['pdflatex', '-interaction=nonstopmode', '-output-directory=build',
           stem + '.tex']
    run(tex)
    if with_bib:
        # bibtex reads build/<stem>.aux and writes build/<stem>.bbl; refs.bib
        # and sn-apanum.bst are found in the working directory, which is HERE.
        run(['bibtex', 'build/' + stem])
    run(tex)
    run(tex)

    log = open(os.path.join(BUILD, stem + '.log'), encoding='utf8', errors='replace').read()
    errors = [l for l in log.split('\n') if l.startswith('!')]
    undef_cite = len(re.findall(r'Warning: Citation .* undefined', log))
    undef_ref = len(re.findall(r'Warning: Reference .* undefined', log))
    missing_fig = len(re.findall(r'File .* not found', log))
    # -output-directory makes pdflatex log an absolute path, which it then
    # wraps across two lines, so anchor the page count on the trailing byte
    # count rather than on "Output written on <file>".
    pages = re.search(r'\((\d+) pages?, \d+ bytes\)', log)
    print('%-22s errors=%d  undefined citations=%d  undefined refs=%d  '
          'missing files=%d  pages=%s'
          % (stem + '.tex', len(errors), undef_cite, undef_ref, missing_fig,
             pages.group(1) if pages else '?'))
    for e in errors[:10]:
        print('    ' + e)

    for name in DELIVERABLES.get(stem, []):
        built = os.path.join(BUILD, name)
        if os.path.exists(built):
            shutil.copy(built, os.path.join(HERE, name))
    return len(errors) + undef_cite + undef_ref + missing_fig


def check_front_matter():
    tex = open(os.path.join(HERE, 'main.tex'), encoding='utf8').read()
    m = re.search(r'\\abstract\{(.*?)\n\n', tex, re.S)
    if m:
        words = len(re.sub(r'[\\{}]', ' ', m.group(1)).split())
        ok = 'ok' if 150 <= words <= 250 else 'OUT OF RANGE (JAAMAS wants 150-250)'
        print('abstract words         : %d  %s' % (words, ok))
    k = re.search(r'\\keywords\{(.*?)\}', tex, re.S)
    if k:
        n = len([x for x in k.group(1).split(',') if x.strip()])
        ok = 'ok' if 4 <= n <= 6 else 'OUT OF RANGE (JAAMAS wants 4-6)'
        print('keywords               : %d  %s' % (n, ok))
    bad = [l for l in tex.split('\n') if '---' in l and not l.lstrip().startswith('%')]
    print('em-dashes in body      : %d %s' % (len(bad), 'ok' if not bad else 'FIX'))

    # Every \includegraphics{FigN} must have a file behind it: a figure that is
    # silently missing still produces a PDF, just with a black box in it.
    cited = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{(Fig\d+)\}', tex)
    have = {f[:-4] for f in os.listdir(os.path.join(HERE, 'figures'))
            if f.endswith('.pdf')}
    lost = [f for f in cited if f not in have]
    spare = sorted(have - set(cited))
    print('figures                : %d cited, %d in figures/ %s'
          % (len(cited), len(have),
             'ok' if not lost and not spare
             else 'MISSING ' + ', '.join(lost) + ' UNUSED ' + ', '.join(spare)))
    return len(lost)


if __name__ == '__main__':
    os.makedirs(BUILD, exist_ok=True)
    targets = sys.argv[1:] or ['main', 'information_sheet', 'cover_letter']
    bad = 0
    for t in targets:
        if os.path.exists(os.path.join(HERE, t + '.tex')):
            bad += latex(t, with_bib=(t == 'main'))
    if 'main' in targets:
        bad += check_front_matter()
    sys.exit(1 if bad else 0)
