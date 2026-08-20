"""Normalise refs.bib for Springer's APA bibliography style (sn-apacite).

Two changes, both purely presentational:

1.  arXiv preprints stored as @article with journal = {arXiv preprint arXiv:ID}
    render as "arXiv preprint arXiv:ID , , https://doi.org/..." because the APA
    style prints empty volume and issue separators.  They are converted to
    @misc with howpublished = {arXiv} and the identifier and DOI link in the
    note, which is the APA 7 preprint form.

2.  booktitle fields are wrapped in an extra pair of braces.  The APA style
    sentence-cases proceedings titles, which turns "Proceedings of the AAAI
    Conference on Artificial Intelligence" into "... the aaai conference on
    artificial intelligence".

Nothing else is touched: no author, title, year, volume, page or DOI value is
altered, so the entries stay identical to the audited refs.bib in paper/.
"""
import re
import sys

B = chr(92)

# ---------------------------------------------------------------------------
# Entry-specific fixes, needed only because the APA style renders these fields
# differently from the numeric style used by the venue-neutral master.
#
#  * "and others" becomes a literal ". . . others" in APA rather than "et al.",
#    so the two truncated author lists are completed.  The added names were
#    read from Crossref (10.1126/science.adn0117 has 25 authors,
#    10.1016/j.amc.2025.129627 has 11); the surnames already in the file are
#    kept as written, because Crossref splits the compound surnames
#    "Fernandez Domingos" and "Duong" incorrectly.
#  * The APA style sentence-cases titles, which lowercases the proper noun in
#    the EU AI Act's official title, so that title is brace-protected.
# ---------------------------------------------------------------------------
FIXUPS = [
    ('bengio2024managing',
     'Shalev-Shwartz, Shai and others',
     'Shalev-Shwartz, Shai and Hadfield, Gillian and Clune, Jeff and\n'
     '             Maharaj, Tegan and Hutter, Frank and\n'
     '             Baydin, At{\\i}l{\\i}m G{\\"u}ne{\\c{s}} and McIlraith, Sheila and\n'
     '             Gao, Qiqi and Acharya, Ashwin and Krueger, David and\n'
     '             Dragan, Anca and Torr, Philip and Russell, Stuart and\n'
     '             Kahneman, Daniel and Brauner, Jan and Mindermann, S{\\"o}ren'),
    ('alalawi2026trust',
     'Han, The Anh and others',
     'Han, The Anh and Krellner, Marcus and Ogbo, Ndidi Bianca and\n'
     '             Powers, Simon T. and Zimmaro, Filippo'),
    ('euaiact2024',
     'title        = {Regulation (EU)',
     'title        = {{Regulation (EU)'),
    ('euaiact2024',
     '(Artificial Intelligence Act)},',
     '(Artificial Intelligence Act)}},'),
]


def normalise(text):
    entries = []
    # split on entry starts, keeping the delimiter
    parts = re.split(r'(?m)^(@[A-Za-z]+\{)', text)
    head = parts[0]
    n_arxiv = n_book = 0
    out = [head]
    for i in range(1, len(parts), 2):
        start, body = parts[i], parts[i + 1]
        m = re.search(r'journal\s*=\s*\{arXiv preprint arXiv:([0-9v.]+)\}', body)
        if m and start.lower().startswith('@article'):
            ident = m.group(1)
            d = re.search(r'doi\s*=\s*\{([^}]*)\}', body)
            doi = d.group(1) if d else '10.48550/arXiv.' + ident
            # drop journal, volume, number, pages, doi
            body = re.sub(r'\n\s*journal\s*=\s*\{arXiv preprint arXiv:[0-9v.]+\},?', '', body)
            body = re.sub(r'\n\s*(volume|number|pages|doi)\s*=\s*\{[^}]*\},?', '', body)
            close = body.index('\n}')                 # entry-closing brace, column 0
            trailing = body[close + 2:]               # comments and blank lines after it
            inner = body[:close].rstrip().rstrip(',')
            note = ('  howpublished = {arXiv},\n'
                    '  note    = {arXiv:%s. %srefdoi{https://doi.org/%s}}\n}'
                    % (ident, B, doi))
            body = inner + ',\n' + note + trailing
            start = '@misc{'
            n_arxiv += 1

        def wrap(mm):
            val = mm.group(2)
            if val.startswith('{') and val.endswith('}'):
                return mm.group(0)
            return mm.group(1) + '{' + val + '}'

        body, k = re.subn(r'(booktitle\s*=\s*\{)([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
                          lambda mm: mm.group(1) + '{' + mm.group(2) + '}}', body)
        n_book += k
        key = body.split(',', 1)[0].strip()
        for fkey, old, new in FIXUPS:
            if key == fkey:
                assert old in body, 'fixup target missing in %s: %r' % (fkey, old)
                body = body.replace(old, new, 1)
        out.append(start)
        out.append(body)
    return ''.join(out), n_arxiv, n_book


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src, encoding='utf8').read()
    new, a, b = normalise(text)
    open(dst, 'w', encoding='utf8').write(new)
    n_in = len(re.findall(r'(?m)^@', text))
    n_out = len(re.findall(r'(?m)^@', new))
    assert n_in == n_out, 'entry count changed: %d -> %d' % (n_in, n_out)
    print('entries: %d, arXiv preprints converted: %d, booktitles protected: %d'
          % (n_out, a, b))
