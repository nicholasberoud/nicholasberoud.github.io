# Repo advisor evidence: website tables

Prepared by Nicholas Beroud on 1 October 2026; selected website adaptation reviewed 1 November 2026.
Original public memo: https://github.com/eleonorabjornberg/repo-market-model/blob/9335638155c46f0f0973fec896de31e9931e4b26/docs/advisor/evidence-pack/MEMO.md
Git blob: e2faba7bacf6b568d86e531234b6b893c5c6f9f0.

These downloads are aggregate tables, not a public release of the private generation pipeline.
The source observations are FRED files downloaded 1 October 2026. Revised historical data are unsuitable for a real-time forecast backtest without a separate availability reconstruction.

distributions.csv: same daily observation counts, medians and 90th percentiles as the memo. IOER before 29 July 2021, IORB thereafter. Common range 3 April 2018 through 30 September 2026. Publication review checked these values against the frozen CSV strings.
episode.csv: dates and original precision clarified against the saved observations. WTREGEN and WRESBAL are weekly averages, weeks ending 8 and 29 October 2025; daily RRP comparisons use 3 and 31 October. They are not simultaneous snapshots. Website display rounds balances to one decimal billion.
balance-groups.csv: unchanged median Thursday–Wednesday mean spreads grouped by Wednesday RRP balance. Right-closed interval labels match the source implementation. They are not estimated breakpoints.

Excluded: daily and weekly threshold-event frequencies, which contain floating-point boundary errors in the original memo; the partially verified SRF proxy table; third-party commentary; the original timeline's incorrect bill-purchase start marker. Original research files and collaborator repositories were not changed. The historical memo still contains those issues.

No causal, predictive or investment conclusion follows from these descriptive comparisons. Eleonora Björnberg owns the model design, implementation and evaluation; this is Nicholas's dated economic-advisory contribution.
