"""Render the already-published repo distribution table, without recalculating data.

Run from the website checkout with a Python environment containing matplotlib:
    MPLCONFIGDIR=/tmp/portfolio-mpl python scripts/render_repo_evidence.py

Only spread-distributions.png is written. The input CSV remains the source of
truth for values, observation counts and date ranges. These are two descriptive
statistics of each period's daily spread distribution, not interval estimates.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "repo-advisor-2026-10"
SOURCE = ASSETS / "distributions.csv"
DESTINATION = ASSETS / "spread-distributions.png"


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    periods = [row["period"] for row in rows]
    if len(periods) != len(set(periods)):
        raise ValueError("Each period must appear only once")

    labels = [
        "2026\nto 30 Sep" if row["period"] == "2026" and row["end_date"] == "2026-09-30"
        else row["period"]
        for row in rows
    ]
    median = [float(row["median_bp"]) for row in rows]
    percentile = [float(row["p90_bp"]) for row in rows]
    y = list(range(len(rows)))
    palette = {"bg": "#0d1117", "text": "#c6cdd5", "grid": "#30363d",
               "median": "#77bdfb", "p90": "#faa356"}
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 22,
        "text.color": palette["text"], "axes.labelcolor": palette["text"],
        "xtick.color": palette["text"], "ytick.color": palette["text"],
        "axes.edgecolor": palette["grid"], "savefig.facecolor": palette["bg"],
    })
    fig, ax = plt.subplots(figsize=(8, 7.3), dpi=120, facecolor=palette["bg"])
    fig.subplots_adjust(left=0.30, right=0.95, top=0.85, bottom=0.16)
    ax.set_facecolor(palette["bg"])
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=palette["grid"], linewidth=0.8)
    ax.axvline(0, color=palette["text"], linewidth=1.4, zorder=1)
    ax.scatter(median, y, s=165, color=palette["median"], marker="o", zorder=3)
    ax.scatter(percentile, y, s=150, color=palette["p90"], marker="D", zorder=3)
    ax.set_yticks(y, labels)
    ax.set_ylim(len(rows) - 0.45, -0.55)
    ax.set_xlim(-12, 12)
    ax.set_xticks([-10, -5, 0, 5, 10])
    ax.set_xlabel("Spread (basis points)", labelpad=16)
    ax.tick_params(axis="y", length=0, pad=15)
    ax.tick_params(axis="x", length=4, pad=9)
    for side in ("top", "left", "right"):
        ax.spines[side].set_visible(False)
    handles = [
        Line2D([], [], linestyle="none", marker="o", markersize=11,
               color=palette["median"], label="Median"),
        Line2D([], [], linestyle="none", marker="D", markersize=10,
               color=palette["p90"], label="90th percentile"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.98),
               frameon=False, ncol=2, columnspacing=1.2, handletextpad=0.45,
               handlelength=0.8, fontsize=21)
    fig.savefig(DESTINATION, dpi=120, metadata={
        "Title": "Historical SOFR minus reserve-interest spread distributions",
        "Description": "Median and 90th percentile of daily spreads in basis points. "
                       "IOER before 29 July 2021, IORB thereafter. Descriptive period "
                       "statistics, not confidence intervals. Source: distributions.csv.",
        "Source": "assets/repo-advisor-2026-10/distributions.csv",
    })
    plt.close(fig)
    print(f"Rendered {DESTINATION.relative_to(ROOT)} from {len(rows)} existing rows.")


if __name__ == "__main__":
    main()
