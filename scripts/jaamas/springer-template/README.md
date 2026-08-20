# Vendored Springer Nature template files

`scripts/build_jaamas.py` reads exactly two files out of Springer's LaTeX
template package, and the package itself is `.gitignore`d because it is a
downloaded archive rather than something authored here. That makes the build
unreproducible from a clean clone, so the two files are vendored:

| file | what the build does with it |
|---|---|
| `sn-jnl.cls` | copied verbatim into `paper-jaamas/` |
| `bst/sn-apacite.bst` | patched into `paper-jaamas/sn-apanum.bst`: the three `SORT` passes are suppressed so the numbered reference list comes out in citation order, and `\begin{thebibliography}{}` is widened to `{999}` so natbib can size numeric labels |

Source: Springer Nature LaTeX template package for journal articles,
`sn-article-template`, December 2024 version, downloaded from
<https://www.springernature.com/gp/authors/campaigns/latex-author-support>.

Both files are distributed under the LaTeX Project Public License, which
permits redistribution. `build_jaamas.py` prefers the downloaded package in
`sn-template-extract/` whenever it is present, so upgrading the template is a
matter of unpacking a newer archive there; these copies are only the fallback.
