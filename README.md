# Nicholas Beroud · personal portfolio

Personal website about markets, policy and research: https://nicholasberoud.github.io/

## Local preview

Run `python3 scripts/build_site.py`, then `python3 -m http.server 4173 --bind 127.0.0.1 --directory _site` from this checkout. Open http://127.0.0.1:4173. Serving the packaged directory also checks that new pages are included in the deployment list.

Plain HTML and CSS with no external runtime dependencies. `index.html` introduces the work; `research.html` carries selected reading notes and current questions; `projects/` and `notes/` contain individual pages. Shared styles are in `assets/style.css`.

## Publishing

GitHub Actions publishes when changes reach `main`. Local first-pass work is not authorization to merge or push. Run `python3 scripts/build_site.py` to package the site and validate internal links, including absolute links to this domain, fragments and duplicate IDs. Actions uploads only `_site/`. Add reviewed new pages to `PAGES` in the build script and reviewed assets to `scripts/public-assets.txt`. The build rejects missing or unlisted assets and symlinks; a filename allowlist does not replace reviewing the file's contents.

The two older note outlines remain in source and are excluded from deployment. Published pages allow search indexing. Private research notes, contact records and correspondence must not enter the public repository or packaged site.

## Content and evidence

- The résumé link retains `assets/nicholas-beroud-resume.pdf`, based on the supplied November 2026 CV, with the public repo-advisor entry corrected to September–October 2026 and past tense. Original application documents are unchanged.
- The Long End lives at `projects/term-premium.html`. The independent Treasury term-premium study is separate from the provisional undergraduate thesis on political credibility and sovereign borrowing in emerging markets. FIMA remains background research.
- Existing quantitative article assets in `assets/term-premium/` are generated outputs from a private research repository. Preserve their dates, definitions, numerical results and captions. Public results downloads do not constitute a release of the full research pipeline.
- `research.html` contains selected, edited reading notes. Reading stages and last-updated dates are explicit. This is not an automatic Notion mirror.
- `notes/tic-research.html` presents a descriptive 2008–2025 holdings series, two charts, data, methods, validation and a curated code snapshot. Data assembly is complete; interpretation remains under review. The note does not identify elasticity or explain term premia. `notes/who-buys-the-debt.html` remains the background explainer.
- The repo-model page credits Eleonora Björnberg as project lead and links Nicholas's dated public advisor evidence pack. It does not imply current decision authority or a public release of the private evidence-generation pipeline.
- EDEN and Embassy descriptions summarize experience without publishing internal work. MineralTrace expansion is deferred.

## Research desk updates

Before adding an entry, verify the source URL and actual reading stage. Record the question, a supported takeaway, connection to a project, what remains unclear and the update date. Separate literature findings from personal findings, and planned analysis from work already executed. Use only public-safe paraphrases and legitimate source links.
