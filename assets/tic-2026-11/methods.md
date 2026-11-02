# TIC holdings: definitions, sources and reproducibility

Public working-note package, 1 November 2026. Descriptive holdings analysis, not a test of investor demand or term-premium causality.

## Scope and sources

The primary vintage is the April 2026 report **Foreign Portfolio Holdings of U.S. Securities, as of June 30, 2025**. Its Treasury blocks in Exhibit 7 (PDF page 20) and Exhibit 8 (PDF page 22) supply the official/private series for 2008–2025. Exhibit 2 (PDF page 10) supplies the separate market-wide denominator.

- Main report: https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/shl2025r.pdf
- Prior vintages: https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/shl2024r.pdf ; https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/shla2016r.pdf ; https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/shla2008r.pdf
- Historical totals: https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/shlhistdat.txt (April 30, 2026 release used in validation; this live URL may later change).
- Official-institution definition: https://home.treasury.gov/tic-country-codes-and-partial-list-of-foreign-official-institutions
- TIC FAQ: https://home.treasury.gov/data/treasury-international-capital-tic-system-home-page/frequently-asked-questions-regarding/ticfaq2
- The 2019 benchmark designation was also verified in the 2019 report introduction: https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/shl2019r.pdf

## Definitions and dates

Amounts are end-June **market values in billions of U.S. dollars**. Annual-survey reporting is at fair value, including short-term securities. Long-term means original maturity over one year; short-term means original maturity of one year or less. This is neither remaining maturity nor the date an investor bought the security. All maturities is the sum of the two categories.

Foreign official institutions include central banks, finance ministries, relevant national agencies, international/regional organizations and banks, corporations or agencies acting as national-government fiscal agents and performing treasury, central-bank, stabilization-fund or exchange-control functions under Treasury’s definition. Government ownership alone does not make every entity official. Private means other foreign holders. Neither classification measures price sensitivity.

The analytical series has 54 rows: 18 years × 3 maturity categories. The separate outstanding-share file has 18 rows. The original source references remain in the `source` column. End-June labels follow the source listing; 2018 and 2019 are June 29 and June 28. The public export normalizes the 2024 `survey_date` to `2024-06-28`, matching the report title and the instruction to report at the last business day of June. Treasury’s listing uses June 30 for that observation. No holdings, computed shares or chart data were changed by this metadata correction.

Benchmark years in this sample are 2009, 2014, 2019 and 2024. Interim annual surveys use a smaller panel and adjustments. Coverage and survey methods can matter for comparisons.

## Two denominators

`official_share_pct = official_bn / total_foreign_bn * 100`: official institutions’ share of **foreign holdings**, for the stated maturity category. The 2025 computed shares are 45.66% long-term, 28.28% short-term and 42.96% all maturities.

`foreign_share_of_outstanding_pct = foreign_owned_bn / treasury_outstanding_mv_bn * 100`: foreign investors’ share of **all marketable Treasury debt at market value**, including U.S. and Federal Reserve holdings in the denominator. This is not a share of total federal debt. The result is 33.47% in 2025.

Published rounded percentages are retained separately from computed percentages. For all maturities, the official share is computed here and has no separate published-percent entry.

## Validation and its limits

The preserved-source run passed source hashes (9 files), official + private = total (36 long/short rows, $1bn tolerance), computed versus published shares (0.15 percentage-point tolerance), historical totals (36 rows), and the Exhibit 2 versus Exhibit 7 + 8 totals (18 years, $1.5bn tolerance). Cross-vintage comparisons found no revisions in 54 overlapping Treasury rows across the selected reports. This is a bounded comparison, not evidence that TIC data never change.

A separate AI reviewer reran extraction, assembly, validation and chart generation in a temporary copy. All nine CSV artifacts and validation.json reproduced byte for byte before the public 2024 date-format correction. The public export preserves all numerical values. These are code/source checks, not external academic peer review or checks claimed to have been personally performed by Nicholas.

The long-term 2024 official/private gap was $3bn, about 0.04% of foreign long-term holdings. Small does not establish that it lies within an estimated revision or rounding band. The first observed crossover in this 2008–2025 sample is 2016 for short-term, 2023 for all maturities and 2025 for long-term.

## Holdings are not transactions

Table 1 of the 2025 report (PDF page 8) reports the 2024–2025 change in foreign official long-term Treasury holdings as approximately −$60bn. Its components are about −$100bn net purchases, +$140bn valuation and −$110bn other adjustments. Rounded components need not sum exactly to the rounded total. The residual must not be omitted. This decomposition is not reconstructed for the entire sample.

Monthly SLT reporting and the Major Foreign Holders estimates are different products. This package does not reconcile monthly positions with annual survey positions. Holdings reporting under SLT began in 2011; later additions changed the form. Do not apply the separate monthly bills valuation convention to the annual fair-value survey.

Custody chains may obscure residence or official status from U.S. reporters. This dataset cannot quantify how much recorded private holdings belong ultimately to official institutions. It cannot identify specific governments behind custodial-center totals, identify investor demand elasticities, or explain term-premium movements.

## Contribution and reproduction

Nicholas framed the question and scope. Extraction and validation code were developed with an AI coding assistant under his direction; interpretation remains under review. Treasury and the Federal Reserve produce the underlying statistics.

The code archive includes the four analysis scripts, verbatim extracted tables, analytical CSVs, chart CSVs, exact dependency requirements, source inventory/hashes and the saved validation report. It excludes private notes, repository history and source PDFs/HTML. Included extracts allow rebuilding the dataset and charts. Re-running PDF extraction and the full source-hash validation requires downloading the original source files at their expected paths; the README and retrieval helper explain this. Live files can change or become unavailable. A changed hash is a vintage mismatch, not a reason to silently accept a new source.

Tested environment: Python 3.13.4, pypdf 6.19.0, matplotlib 3.11.0. The pypdf version matters for extraction of these particular PDF layouts.

## Additional source review, 1 November 2026

In an AI-assisted source review, five long-term Treasury rows (2008, 2016, 2021, 2024 and 2025) were checked visually against Exhibit 7 of the 2025 report, printed page 19 / PDF page 20. Official holdings, private holdings, totals and published official percentages matched both the source-package dataset and the website export. This is a spot-check, not a second extraction of every observation.

The 2019 report introduction, printed page 1 / PDF page 7, explicitly identifies that survey as a benchmark. The 2024 report cover uses June 28; Treasury’s online listing labels it June 30. Treasury’s SHL/SHLA forms page also confirms June 28 for the 2024 benchmark and records a correction to the earlier date notice. The export follows that reference date as documented above. Corrected notice (June 5, 2024, p.48218): https://treasury.gov/resource-center/data-chart-center/tic/Documents/frshl2024%282024-06%29.pdf . Forms and archived instructions: https://home.treasury.gov/data/treasury-international-capital-tic-system-home-page/tic-forms-instructions/forms-shl

Section 4.3.2 of the 2025 report, printed page 52 / PDF page 53, refers to “the 2024 SHL” while discussing “this survey.” This is an internal wording inconsistency, not a verified correction notice. Treasury’s SHL/SHLA forms page explicitly identifies SHLA (2025) as an annual survey following the 2024 benchmark. That explicit description, rather than the inconsistent sentence, supports the 2025 annual classification.
