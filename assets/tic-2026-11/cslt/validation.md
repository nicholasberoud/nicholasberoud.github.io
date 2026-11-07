# CSLT decomposition: validation

Source: `cslt_20261107.zip`, transmitted 2026-10-13 15:18:48.221676.

| Check | Result | Detail |
|---|---|---|
| C1 Source file hash matches manifest | pass | cslt_20261107.zip sha256 40bc8ffe3fcf5b56 |
| C2 Official + non-official = grand total (holdings, net purchases, valuation) | pass | 1500 comparisons; largest gap $0.0m |
| C3 change = net purchases + valuation + other, every row | pass | largest error $0.00m over 1500 rows |
| C4 No missing months in the main window | pass | 43 months, 2023-02 to 2026-08; missing [] |
| C5 Net purchases are the published foreign net transactions (positive = foreigners bought) | pass | Series for_lt_treas_net_*: "foreign investors' net purchases, at market value" (series notes); used unchanged. |

Not yet done: a cross-check against Treasury SLT Table 3 for February 2023 onward, and two or three months checked by hand against Treasury releases.
