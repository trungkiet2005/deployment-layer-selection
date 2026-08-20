"""Compile the JAAMAS manuscript and the two accompanying documents.

    python build.py            main.tex, information_sheet.tex, cover_letter.tex
    python build.py main       only the manuscript

Runs pdflatex / bibtex / pdflatex / pdflatex and then reports the things the
journal actually checks: LaTeX errors, undefined citations and references,
abstract word count, keyword count and page count.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    return subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                          encoding='utf8', errors='replace')


def latex(stem, with_bib=True):
    run(['pdflatex', '-interaction=nonstopmode', stem + '.tex'])
    if with_bib:
        run(['bibtex', stem])
    run(['pdflatex', '-interaction=nonstopmode', stem + '.tex'])
    run(['pdflatex', '-interaction=nonstopmode', stem + '.tex'])

    log = open(os.path.join(HERE, stem + '.log'), encoding='utf8', errors='replace').read()
    errors = [l for l in log.split('\n') if l.startswith('!')]
    undef_cite = len(re.findall(r'Warning: Citation .* undefined', log))
    undef_ref = len(re.findall(r'Warning: Reference .* undefined', log))
    pages = re.search(r'Output written on \S+ \((\d+) pages?', log)
    print('%-22s errors=%d  undefined citations=%d  undefined refs=%d  pages=%s'
          % (stem + '.tex', len(errors), undef_cite, undef_ref,
             pages.group(1) if pages else '?'))
    for e in errors[:10]:
        print('    ' + e)
    return len(errors) + undef_cite + undef_ref


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


if __name__ == '__main__':
    targets = sys.argv[1:] or ['main', 'information_sheet', 'cover_letter']
    bad = 0
    for t in targets:
        if os.path.exists(os.path.join(HERE, t + '.tex')):
            bad += latex(t, with_bib=(t == 'main'))
    if 'main' in targets:
        check_front_matter()
    sys.exit(1 if bad else 0)
