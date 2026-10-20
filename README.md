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
- Projects, in homepage order: the FIMA Repo Facility (undergraduate thesis direction, no findings), the Term Premium Research Journal, and the Repo Market Model collaboration.
- The journal lives at `projects/term-premium.html` (stable route) with dated articles under `projects/term-premium/`. Each article's figures, chart data and generated results file are in `assets/term-premium/<yyyy-mm>/`, copied from the private research repository's generated outputs; numbers on the page come from that results file. The research repository itself is not linked.
- Notes include a short team hackathon recap and a standalone explainer on Treasury holders and price sensitivity.
- The repo-model page credits Eleonora Björnberg and links to her original public project.
