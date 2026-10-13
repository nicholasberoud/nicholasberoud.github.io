# Nicholas Beroud · personal portfolio

Personal website about markets, policy and technology: https://nicholasberoud.github.io/

## Preview

Run `python3 -m http.server 4173 --bind 127.0.0.1` from this directory, then visit http://127.0.0.1:4173.

Plain HTML and CSS, with no external runtime dependencies. `index.html` contains the introduction and listings; `projects/` and `notes/` contain individual pages; `assets/style.css` controls the shared appearance.

## Publishing

GitHub Actions publishes reviewed content to GitHub Pages when changes reach `main`. Run `python3 scripts/build_site.py` locally to package the site and validate its internal links. The workflow uploads only the resulting `_site/` folder. Add reviewed new pages to `PAGES` in that script before linking them.

The two older note outlines remain in source for future writing and are excluded from deployment. Published pages allow search indexing.

## Content

- The résumé icon opens the supplied October 2026 PDF in a new tab. `assets/nicholas-beroud-resume.pdf` is unchanged from the supplied file; the link has no download attribute.
- Notes include a short team hackathon recap and a sourced thesis explainer.
- The thesis page uses its full title, an existing research figure (9 October 2026 vintage), and an institutional hypothesis with limitations. Its private research repository is not linked.
- The repo-model page credits Eleonora Björnberg and links to her original public project.
