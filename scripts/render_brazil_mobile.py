"""Phone-width versions of the Brazil market-note exhibits, plus a labelled desktop Exhibit 1.

Presentation only. The sole numerical inputs are the chart-data CSVs the site already
publishes in assets/term-premium/brazil-2026-10/; no value is changed, estimated or
downloaded. Style follows the site's house chart style (portfolio-projects
projects/site/charts/restyle.py, SITE-11): Inter, the GitHub dark surface and the
Brazil flag colours. Writes PNGs plus mobile/provenance.json with source hashes.

Usage: python3 scripts/render_brazil_mobile.py   (needs matplotlib, numpy, Inter font)
"""
import csv, hashlib, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets/term-premium/brazil-2026-10'
OUT = SRC / 'mobile'
OUT.mkdir(exist_ok=True)

BG, GRID, ZERO, INK, MUTED = '#0d1117', '#1f252d', '#6e7681', '#c6cdd5', '#89929b'
BR = {'green': '#2fbf71', 'yellow': '#ffdf00', 'blue': '#4d8fe0', 'grey': '#89929b'}
DPI, LW = 200, 2.0
plt.rcParams.update({
    'font.family': 'Inter', 'font.size': 15, 'text.color': INK,
    'axes.facecolor': BG, 'figure.facecolor': BG, 'savefig.facecolor': BG,
    'axes.edgecolor': BG, 'axes.labelcolor': MUTED, 'axes.labelsize': 14.5,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'xtick.labelsize': 14.5, 'ytick.labelsize': 14.5,
    'legend.fontsize': 15, 'lines.linewidth': LW, 'lines.solid_capstyle': 'round',
    'svg.hashsalt': 'nicholas-brazil-mobile', 'path.simplify': False,
})
read = []

def rows(name):
    p = SRC / name
    read.append({'file': f'assets/term-premium/brazil-2026-10/{name}', 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    return list(csv.DictReader(open(p)))

def clean(ax, right=True):
    for s in ax.spines.values():
        s.set_visible(False)
    (ax.yaxis.tick_right if right else ax.yaxis.tick_left)()
    ax.tick_params(which='both', length=0, pad=6)
    ax.grid(axis='y', color=GRID, lw=0.8)
    ax.set_axisbelow(True)

fl = lambda s: float(s) if s not in ('', None) else np.nan
written = []

def save(fig, path):
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    written.append(str(path.relative_to(ROOT)))

# ---- Exhibit 1: cross-asset panels ----
PANELS = [('USD/BRL', 'USD/BRL, reais per dollar', BR['yellow'], lambda v: f'{v:.2f}'),
          ('Ibovespa', 'Ibovespa, thousand points', BR['green'], lambda v: f'{v:,.0f}'),
          ('EWZ NAV', 'EWZ, NAV per share (US$)', BR['green'], lambda v: f'{v:,.0f}'),
          ('NTN-F Jan 2037', 'NTN-F Jan 2037 yield, % a year', BR['blue'], lambda v: f'{v:.1f}')]
ca = rows('br-cross-asset.csv')
EV = np.datetime64('2026-10-26')
TICKS = [np.datetime64(f'2026-10-{k}') for k in (16, 19, 23, 26, 29)]

def cross_asset(axes, title_size, label_first):
    for i, (ax, (key, title, c, f)) in enumerate(zip(axes, PANELS)):
        clean(ax)
        p = [x for x in ca if x['panel'] == key]
        d = np.array([np.datetime64(x['date']) for x in p]); v = np.array([fl(x['value']) for x in p])
        if key == 'Ibovespa' and v.max() > 1000:
            v = v / 1000
        ax.plot(d, v, color=c)
        ax.axvline(EV, color=MUTED, lw=0.9, ls=(0, (2, 2)))
        ax.yaxis.set_major_locator(MaxNLocator(3)); ax.yaxis.set_major_formatter(FuncFormatter(lambda t, _, f=f: f(t)))
        ax.set_xticks(TICKS); ax.set_xticklabels(['16', '19', '23', '26', '29'])
        ax.text(0, 1.06, title, transform=ax.transAxes, fontsize=title_size, color=INK, va='bottom')
        if i == 0 and label_first:
            ax.text(EV, 1.06, 'Monday after the runoff', transform=ax.get_xaxis_transform(), fontsize=title_size - 1.5,
                    color=MUTED, ha='center', va='bottom')

fig, axes = plt.subplots(4, 1, figsize=(4.3, 10.4))
cross_asset(axes, 15, True)
axes[0].texts[-1].set_position((EV, 1.32))
axes[-1].set_xlabel('October 2026', loc='left')
fig.subplots_adjust(left=0.04, right=0.84, top=0.93, bottom=0.07, hspace=0.72)
save(fig, OUT / 'br-cross-asset.png')

# Desktop Exhibit 1 with the year and the runoff label (same layout as the house style).
plt.rcParams.update({'font.size': 12, 'xtick.labelsize': 11.5, 'ytick.labelsize': 11.5, 'lines.linewidth': 1.6})
fig, axes = plt.subplots(2, 2, figsize=(8.6, 4.6025), gridspec_kw={'hspace': 0.75, 'wspace': 0.28})
cross_asset(axes.ravel(), 11.5, False)
for ax in axes[1]:
    ax.set_xlabel('October 2026', loc='left', fontsize=11)
axes[0, 1].text(EV - np.timedelta64(4, 'h'), 0.06, 'Monday after the runoff', transform=axes[0, 1].get_xaxis_transform(),
                fontsize=9.5, color=MUTED, ha='right', va='bottom')
fig.subplots_adjust(left=0.03, right=0.92, top=0.9, bottom=0.13)
save(fig, SRC / 'br-cross-asset.png')
plt.rcParams.update({'font.size': 15, 'xtick.labelsize': 14.5, 'ytick.labelsize': 14.5, 'lines.linewidth': LW})

# ---- Exhibit 2: fat tails ----
ft = rows('br-fat-tails.csv')
lft = np.array([fl(x['bin_left_pct']) for x in ft]); rgt = np.array([fl(x['bin_right_pct']) for x in ft])
obs = np.array([fl(x['observed_days']) for x in ft]); exp_ = np.array([fl(x['normal_expected_days']) for x in ft])
worst = rows('top10_down_days.csv')[0]; wv = fl(worst['return_pct'])
fig, ax = plt.subplots(figsize=(4.3, 5.4)); clean(ax)
m = obs > 0
ax.bar(lft[m], obs[m], width=(rgt - lft)[m] * 0.72, align='edge', color=BR['green'], lw=0)
mid = (lft + rgt) / 2; keep = exp_ >= 0.3
ax.plot(mid[keep], exp_[keep], color=BR['yellow'])
ax.set_yscale('log'); ax.set_ylim(0.6, 3000)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: '1,000 days' if v == 1000 else f'{v:,.0f}'))
ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, p: ''))
ax.annotate(f'26 Oct\n2026\n{wv:.1f}%'.replace('-', '−'), (wv, 1.15), xytext=(-20.5, 9), fontsize=13.5, color=INK,
            va='bottom', ha='left', linespacing=1.25, arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.9))
ax.set_xticks([-20, -10, 0, 10, 20]); ax.set_xticklabels(['−20', '−10', '0', '10', '20'])
ax.set_xlabel('EWZ daily return, %')
ax.axvline(0, color=ZERO, lw=0.9, zorder=1)
handles = [Line2D([0], [0], color=c, lw=3) for c in (BR['green'], BR['yellow'])]
ax.legend(handles, ['Actual days', 'Normal curve'], loc='lower left', bbox_to_anchor=(0, 1.02), ncol=2, frameon=False,
          handlelength=1.1, columnspacing=1.4, labelcolor=INK, borderaxespad=0)
fig.subplots_adjust(left=0.04, right=0.71, top=0.9, bottom=0.12)
save(fig, OUT / 'br-fat-tails.png')

# ---- Exhibit 3: decomposition (labels above bars for a narrow screen) ----
dc = rows('br-decomposition.csv')
cols = [BR['green'], BR['yellow'], BR['grey'], BR['blue']]
fig, ax = plt.subplots(figsize=(4.3, 5.0)); clean(ax, right=False)
ax.grid(axis='y', visible=False); ax.grid(axis='x', color=GRID, lw=0.8)
n = len(dc)
for i, (x, c) in enumerate(zip(dc, cols)):
    y = (n - 1 - i) * 1.6
    s, ch = fl(x['start_pct']), fl(x['change_pct'])
    left, width = (0, fl(x['end_pct'])) if i == n - 1 else (s, ch)
    ax.barh(y, width, left=left, color=c, height=0.62)
    val = (f'{ch:+.1f}%' if i < n - 1 else f'{fl(x["end_pct"]):.1f}%').replace('-', '−')
    ax.text(-26.5, y + 0.55, x['bar'], fontsize=14.5, color=INK, va='bottom', ha='left')
    ax.text(min(left, left + width) - 0.4, y, val, va='center', ha='right', fontsize=14.5, color=INK)
ax.set_yticks([])
ax.axvline(0, color=ZERO, lw=0.9, zorder=1)
ax.set_xlim(-27, 1.5); ax.set_ylim(-0.7, (n - 1) * 1.6 + 1.3)
ax.set_xticks([-25, -20, -15, -10, -5, 0]); ax.set_xticklabels(['−25', '−20', '−15', '−10', '−5', '0'])
ax.set_xlabel('Return on 26 October 2026, %')
fig.subplots_adjust(left=0.04, right=0.97, top=0.97, bottom=0.12)
save(fig, OUT / 'br-decomposition.png')

# ---- Exhibit 4: gross debt ----
db = rows('br-debt.csv')
yr = np.array([int(x['year']) for x in db]); v = np.array([fl(x['gross_debt_pct_gdp']) for x in db])
fig, ax = plt.subplots(figsize=(4.3, 4.4)); clean(ax)
ax.plot(yr, v, color=BR['blue']); ax.plot(yr[-1], v[-1], marker='o', ms=7, color=BR['blue'], mec=BG, mew=1.2)
ax.annotate(f'{yr[-1]}: {v[-1]:.1f}%', (yr[-1], v[-1]), xytext=(0, 16), textcoords='offset points', ha='right',
            fontsize=14.5, color=INK)
ax.set_ylim(40, 108); ax.yaxis.set_major_locator(MaxNLocator(4))
ax.yaxis.set_major_formatter(FuncFormatter(lambda t, p: f'{t:,.0f}'))
ax.set_xticks([2000, 2010, 2020])
ax.text(0, 1.04, 'Gross debt, % of GDP (IMF)', transform=ax.transAxes, fontsize=15, color=INK, va='bottom')
fig.subplots_adjust(left=0.04, right=0.84, top=0.88, bottom=0.1)
save(fig, OUT / 'br-debt.png')

(OUT / 'provenance.json').write_text(json.dumps({
    'script': 'scripts/render_brazil_mobile.py', 'inputs': read, 'outputs': written,
    'note': 'Presentation only: values read from the published chart-data CSVs; nothing estimated or changed.'}, indent=1) + '\n')
print('\n'.join(written))
