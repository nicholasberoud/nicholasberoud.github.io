"""Draw the two homepage-card charts for the neocloud study (CoreWeave).

Presentation only: every plotted value and every number in a callout comes from
assets/neocloud-2026-11/coreweave/data.json (written by extract_coreweave.py).
Same canvas, fonts and axis style as scripts/render_treasury_charts.py, in the
study's own colours. Writes PNG and SVG pairs to assets/neocloud-2026-11/coreweave/.
Usage: python3 scripts/neocloud/render_card_charts.py  (needs matplotlib)
"""
import json
import os
from datetime import date
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/nicholas-neocloud-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/neocloud-2026-11/coreweave'
D = json.loads((OUT / 'data.json').read_text())
F = D['facts']
BG, FG, MUTED, GRID, REF = '#0d1117', '#e6edf3', '#9da7b3', '#29323d', '#c6cdd5'
VIOLET, GOLD, AQUA, GROSS = '#9085e9', '#c98500', '#199e70', '#b1bac4'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 18, 'xtick.labelsize': 18, 'ytick.labelsize': 18,
    'text.color': FG, 'xtick.color': MUTED, 'ytick.color': MUTED,
    'figure.facecolor': BG, 'axes.facecolor': BG, 'savefig.facecolor': BG,
    'svg.fonttype': 'none', 'svg.hashsalt': 'nicholas-neocloud-2026-11',
    'path.simplify': False, 'lines.solid_capstyle': 'round',
})


def year(iso):
    d = date.fromisoformat(iso)
    return d.year + (d.timetuple().tm_yday - 1) / 365.0


X = [year(d['iso']) for d in D['dates']]
TICKS = [(year('2023-12-31'), 'Dec 2023'), (year('2024-12-31'), 'Dec 2024'), (year('2025-12-31'), 'Dec 2025'), (year('2026-09-30'), 'Sep 2026')]


def canvas():
    fig = plt.figure(figsize=(8.6, 6.3), dpi=200)
    ax = fig.add_axes([.065, .14, .81 - .065, .80 - .14])
    ax.set_axisbelow(True)
    for side in ('top', 'left', 'right'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)
    ax.spines['bottom'].set_linewidth(.7)
    ax.tick_params(axis='both', length=0, pad=10)
    ax.yaxis.tick_right()
    ax.grid(axis='y', color=GRID, lw=.7)
    ax.set_xlim(X[0] - .08, X[-1] + .08)
    ax.set_xticks([t for t, _ in TICKS])
    ax.set_xticklabels([l for _, l in TICKS])
    return fig, ax


def ticks(ax, vals, fmt_top):
    ax.set_yticks(vals)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: fmt_top(x) if x == max(vals) else f'{x:,.0f}'))


def legend(fig, items, fontsize=16.5):
    handles = [Line2D([], [], color=c, lw=3, linestyle=ls, label=l) for l, c, ls in items]
    fig.legend(handles=handles, loc='upper left', bbox_to_anchor=(.055, .94), ncol=len(items), frameon=False,
               fontsize=fontsize, handlelength=1.25, handletextpad=.5, columnspacing=1.15, labelcolor=FG, borderaxespad=0)


def callout(ax, x, y, label, xytext):
    ax.scatter([x], [y], s=25, color=FG, zorder=6)
    ax.annotate(label, xy=(x, y), xytext=xytext, textcoords='data', ha='left', va='center', color=FG, fontsize=16,
                arrowprops={'arrowstyle': '-', 'color': FG, 'lw': .8, 'shrinkA': 6, 'shrinkB': 5},
                bbox={'facecolor': BG, 'edgecolor': 'none', 'pad': 2.5, 'alpha': .94}, zorder=7)


def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=200)
    fig.savefig(OUT / f'{name}.svg', metadata={'Date': None, 'Creator': 'Neocloud card renderer'})
    plt.close(fig)


def debt_over_assets():
    hd, lid = D['ex1']['series']
    fig, ax = canvas()
    ax.plot(X, hd['pct_assets'], color=VIOLET, lw=2.4)
    ax.plot(X, lid['pct_assets'], color=GOLD, lw=2.4, ls=(0, (6, 2)))
    legend(fig, [('Headline Debt', VIOLET, '-'), ('Lease-Inclusive Debt', GOLD, '--')])
    ax.set_ylim(0, 82)
    ticks(ax, [0, 20, 40, 60, 80], lambda x: f'{x:.0f}%')
    ax.axhline(0, color=REF, lw=.9)
    assert abs(hd['pct_assets'][-1] - float(F['hd_pct_2026']['exact'])) < 1e-9
    callout(ax, X[-1], hd['pct_assets'][-1], f"Debt is {F['hd_pct_2026']['shown']}\nof assets, up\nfrom {F['hd_pct_2023']['shown']}", (2025.75, 24))
    save(fig, 'card-debt-over-assets')


def debt_and_equipment():
    s = {x['id']: x for x in D['ex5']['series']}
    fig, ax = canvas()
    ax.plot(X, s['gross']['usd_bn'], color=GROSS, lw=2.0, ls=(0, (5, 3)))
    ax.plot(X, s['headline']['usd_bn'], color=VIOLET, lw=2.4)
    ax.plot(X, s['tech']['usd_bn'], color=AQUA, lw=2.4)
    legend(fig, [('Debt', VIOLET, '-'), ('GPU proxy', AQUA, '-'), ('All PP&E', GROSS, '--')])
    ax.set_ylim(0, 70)
    ticks(ax, [0, 20, 40, 60], lambda x: f'${x:.0f}bn')
    ax.axhline(0, color=REF, lw=.9)
    assert abs(s['headline']['usd_bn'][-1] * 1000 - float(F['hd_2026']['exact'])) < 1e-6
    callout(ax, X[-1], s['headline']['usd_bn'][-1], f"Debt {F['hd_2026']['shown']},\nequipment {F['tech_2026']['shown']}", (2024.35, 40))
    save(fig, 'card-debt-and-equipment')


if __name__ == '__main__':
    debt_over_assets()
    debt_and_equipment()
    print('Rendered 2 card charts from data.json')
