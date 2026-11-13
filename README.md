# Nicholas Beroud · personal portfolio

Personal website about markets, policy and research: https://nicholasberoud.github.io/

## Local preview

Run `python3 scripts/build_site.py`, then `python3 -m http.server 4173 --bind 127.0.0.1 --directory _site` from this checkout. Open http://127.0.0.1:4173. Serving the packaged directory also checks that new pages are included in the deployment list.

Plain HTML and CSS with no external runtime dependencies. `index.html` opens with Nicholas’s introduction, then a featured Treasury research project and other Projects (a grid), the undergraduate thesis and Experience; `research.html` lists every project in detail; `thesis.html` is the thesis page; `projects/` and `notes/` contain individual pages. Shared styles are in `assets/style.css`.

## Publishing

GitHub Actions publishes when changes reach `main`. Local first-pass work is not authorization to merge or push. Run `python3 scripts/build_site.py` to package the site and validate internal links, including absolute links to this domain, fragments and duplicate IDs. Actions uploads only `_site/`. Add reviewed new pages to `PAGES` in the build script and reviewed assets to `scripts/public-assets.txt`. The build rejects missing or unlisted assets and symlinks; a filename allowlist does not replace reviewing the file's contents.

The two older note outlines remain in source and are excluded from deployment. Published pages allow search indexing. Private research notes, contact records and correspondence must not enter the public repository or packaged site.

## Content and evidence

- The résumé link retains `assets/nicholas-beroud-resume.pdf`, based on the supplied November 2026 CV, with the public repo-advisor entry corrected to September–October 2026 and past tense. Original application documents are unchanged.
- `projects/us-treasury-markets.html` integrates the complete pricing study and annual foreign-ownership investigation into one research article. The monthly follow-up remains separate. It explicitly connects the post-2008 pricing puzzle to investigating ownership, without claiming a joint causal test. Existing article URLs and evidence are retained. The undergraduate thesis stays separate. `projects/term-premium.html` remains a legacy redirect; `projects/fima.html` stays in source and is not deployed.
- Existing quantitative article assets in `assets/term-premium/` are generated outputs from a private research repository. Preserve their dates, definitions, numerical results and captions. Public results downloads do not constitute a release of the full research pipeline.
- `research.html` lists the featured Treasury project and the other research and collaborative projects. It is not an automatic Notion mirror.
- `notes/tic-research.html` presents a descriptive 2008–2025 holdings series, two charts, data, methods, validation and a curated code snapshot. Data assembly is complete; interpretation remains under review. The note does not identify elasticity or explain term premia. The earlier ownership page remains accessible as a source version. `notes/who-buys-the-debt.html` redirects to the price-sensitivity section of the integrated article.
- The repo-model contribution remains a separate collaborative project. Its page credits Eleonora Björnberg as project lead and links Nicholas's dated public advisor evidence pack. Its chart is a presentation of the unchanged public `distributions.csv`, generated with `scripts/render_repo_evidence.py`. It does not imply current decision authority or a public release of the private evidence-generation pipeline.
- EDEN and Embassy descriptions summarize experience without publishing internal work. MineralTrace expansion is deferred.

## Research updates

Before adding an entry, verify the source URL and actual reading stage. Record the question, a supported takeaway, connection to a project, what remains unclear and the update date. Separate literature findings from personal findings, and planned analysis from work already executed. Use only public-safe paraphrases and legitimate source links.

## Treasury integration review · 13 November 2026

The integrated article follows the weaker estimated deficit–term-premium relationship into a foreign-holder premise check and discussion of price sensitivity. Original prose, all nine exhibits (including the estimates table), technical methods and source downloads are retained. The transactions-versus-valuation draft is excluded from this article. The annual holdings series begins in 2008 and cannot itself identify the before/after change. The monthly follow-up remains a draft with external/source checks outstanding. All existing numerical artifacts are preserved. Two inherited sentences were corrected against saved evidence: the main study's overgeneralised debt-coefficient range, and the monthly note's categorical custody attribution. No estimates were rerun. Local preview and review do not authorize publication.

The eight integrated-article charts use coordinated blue, teal and amber presentation exports in `assets/treasury-2026-11/`. Run `python3 scripts/render_treasury_charts.py` with matplotlib, numpy and pandas to reproduce them from the existing public CSVs and saved annual-regression coefficients. PNG and SVG files are provided; `presentation-provenance.json` records source hashes, row counts and checks. Original chart assets and numerical artifacts are retained unchanged.
