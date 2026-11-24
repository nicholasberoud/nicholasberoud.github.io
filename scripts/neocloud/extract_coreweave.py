"""Extract the CoreWeave case-study data from the private research repository.

Reads only SEC-derived files from nicholasberoud/ai-compute-economics
(stage 3 results, the note's figure CSVs and the workbook's figure data),
plus the workbook's Sources and Evidence Index sheets for filing names,
SEC.gov links and printed pages. Writes the public outputs in
assets/neocloud-2026-11/coreweave/:

  data.json        every chart series and every number shown on the page
  numbers.csv      one row per displayed number: shown text, exact value, source CSV, row, column, filing, page
  exhibit-*.csv    the plotted values of each exhibit, with filing and page
  provenance.json  research commit and SHA-256 of every input file

Usage: python3 scripts/neocloud/extract_coreweave.py --research ../ai-compute-economics

Nothing from Bloomberg, private/ or results_*.csv is read. The workbook and
the PDF note are not copied.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/neocloud-2026-11/coreweave'

S3 = 'research/coreweave/stage3/rq1_results'
FIG = 'research/coreweave/stage5/rq1_note/out'
WB = '{wb}'  # the stage 5 workbook folder, found in main() by the workbook's file name
INPUTS = {
    'leverage_table': f'{S3}/leverage_table.csv',
    'instrument_mix': f'{S3}/instrument_mix.csv',
    'instrument_lines': f'{S3}/instrument_lines.csv',
    'ppe_categories': f'{S3}/ppe_categories.csv',
    'sources_uses': f'{S3}/sources_uses.csv',
    'routes_dated': f'{S3}/routes_dated.csv',
    'collateral_dated': f'{S3}/collateral_dated.csv',
    'facility_cases': f'{S3}/facility_cases.csv',
    'facility_security_timeline': f'{S3}/facility_security_timeline.csv',
    'note_issue_uses': f'{S3}/note_issue_uses.csv',
    'oem_case': f'{S3}/oem_case.csv',
    'fig1_debt_leverage': f'{FIG}/fig1_debt_leverage.csv',
    'fig2_instrument_mix': f'{FIG}/fig2_instrument_mix.csv',
    'fig3_ppe_composition': f'{FIG}/fig3_ppe_composition.csv',
    'figures_data': f'{WB}/figures/figures_data.csv',
}
WORKBOOK = f'{WB}/CoreWeave_RQ1_Debt_and_Leverage.xlsx'  # read for Sources and Evidence Index only

DATES = ['2023-12-31', '2024-12-31', '2025-03-31', '2025-06-30', '2025-09-30',
         '2025-12-31', '2026-03-31', '2026-06-30', '2026-09-30']
WB_COL = dict(zip(['FY 2023', 'FY 2024', 'Q1 2025', 'Q2 2025', 'Q3 2025', 'FY 2025', 'Q1 2026', 'Q2 2026', 'Q3 2026'], DATES))
MONTH = {'03': 'Mar', '06': 'Jun', '09': 'Sep', '12': 'Dec'}

# source_id in the research CSVs -> document name on the workbook's Sources sheet, and a short label
DOCS = {
    'crwv-424b4-20250331': ('IPO Prospectus (Form 424B4)', 'IPO prospectus'),
    'crwv-10q-20250515': ('Form 10-Q for Q1 2025', '10-Q, Q1 2025'),
    'crwv-10q-20250813': ('Form 10-Q for Q2 2025', '10-Q, Q2 2025'),
    'crwv-10q-20251113': ('Form 10-Q for Q3 2025', '10-Q, Q3 2025'),
    'crwv-10k-20260302': ('Form 10-K for 2025', '10-K, 2025'),
    'crwv-10q-20260508': ('Form 10-Q for Q1 2026', '10-Q, Q1 2026'),
    'crwv-10q-20260812': ('Form 10-Q for Q2 2026', '10-Q, Q2 2026'),
    'crwv-10q-20261112': ('Form 10-Q for Q3 2026', '10-Q, Q3 2026'),
    'crwv-s1-20250303-ex-10-13': ('DDTL 2.0 Credit Agreement (S-1 Exhibit 10.13)', 'S-1 Ex. 10.13'),
    'crwv-s1-20250303-ex-10-16': ('DDTL 2.0 Parent Guarantee and Pledge Agreement (S-1 Exhibit 10.16)', 'S-1 Ex. 10.16'),
    'crwv-8k-20251002-ex-10-1': ('Fifth Amendment to the DDTL 2.0 Credit Agreement (8-K Exhibit 10.1)', '8-K Ex. 10.1 (Oct 2025)'),
    'crwv-8k-20260331': ('Form 8-K Announcing DDTL 4.0', '8-K, 31 Mar 2026'),
    'crwv-8k-20260331-ex-10-1': ('DDTL 4.0 Credit Agreement (8-K Exhibit 10.1)', '8-K Ex. 10.1 (Mar 2026)'),
    'crwv-8k-20260331-ex-10-2': ('DDTL 4.0 Limited Guarantee (8-K Exhibit 10.2)', '8-K Ex. 10.2'),
    'crwv-8k-20260331-ex-99-1': ('DDTL 4.0 Press Release (8-K Exhibit 99.1)', '8-K Ex. 99.1'),
}
# the balance sheet behind each reporting date (Evidence Index row 1.27)
BALANCE_SHEET = {
    '2023-12-31': ('crwv-424b4-20250331', 'F-4'), '2024-12-31': ('crwv-424b4-20250331', 'F-4'),
    '2025-03-31': ('crwv-10q-20250515', '6'), '2025-06-30': ('crwv-10q-20250813', '6'),
    '2025-09-30': ('crwv-10q-20251113', '6'), '2025-12-31': ('crwv-10k-20260302', '84'),
    '2026-03-31': ('crwv-10q-20260508', '6'), '2026-06-30': ('crwv-10q-20260812', '6'),
    '2026-09-30': ('crwv-10q-20261112', '6'),
}
# debt lines whose printed names change between filings -> one facility lane
LANE = {
    'Delayed Draw Term Loan Facility 1.0': 'DDTL 1.0', 'DDTL 1.0 Facility': 'DDTL 1.0',
    'Delayed Draw Term Loan Facility 2.0': 'DDTL 2.0', 'DDTL 2.0 Facility': 'DDTL 2.0',
    'DDTL 2.1 Facility': 'DDTL 2.1', 'DDTL 3.0 Facility': 'DDTL 3.0',
    'DDTL 4.0 Facility(1)': 'DDTL 4.0', 'DDTL 4.0 Facility': 'DDTL 4.0',
    'DDTL 5.0 Facility': 'DDTL 5.0', 'DDTL 5.5 Facility': 'DDTL 5.5',
    '2024 Term Loan Facility': '2024 Term Loan', 'Revolving Credit Facility': 'Revolving credit facility',
    'Magnetar Loan': 'Magnetar loan',
    'Original Equipment Manufacturer financing arrangements': 'OEM and software financing',
    'OEM Financing Arrangements': 'OEM and software financing',
    'OEM and Software License Financing Arrangements': 'OEM and software financing',
    '2022 Senior Secured Notes': '2022 Senior Secured Notes', '2030 Senior Notes': '2030 Senior Notes',
    '2031 Senior Notes': '2031 9.00% Senior Notes', '2031 9.00% Senior Notes': '2031 9.00% Senior Notes',
    '2031 9.75% Senior Notes': '2031 9.75% Senior Notes', '2032 9.625% Senior Notes': '2032 9.625% Senior Notes',
    '2032 EUR Senior Notes(1)': '2032 EUR Senior Notes',
    '2021 Convertible Senior Secured Notes': '2021 Convertible Senior Secured Notes',
    '2031 Convertible Senior Notes': '2031 Convertible Senior Notes',
    '2032 Convertible Senior Notes': '2032 Convertible Senior Notes',
    '2033 Convertible Senior Notes': '2033 Convertible Senior Notes',
    'Convertible Promissory Notes': 'Convertible promissory notes',
}
TYPE_ORDER = ['Delayed-draw term loans (DDTL)', 'Term loans', 'Convertible notes', 'Senior notes',
              'Revolving credit facility', 'OEM and software financing', 'Other loans (Magnetar)']


def D(x):
    return Decimal(str(x))


def rnd(x, places):
    q = Decimal(1).scaleb(-places)
    return D(x).quantize(q, rounding=ROUND_HALF_UP)


def label(iso):
    return f'{MONTH[iso[5:7]]} {iso[:4]}'


def read(rel, research):
    with open(research / rel, newline='') as f:
        return list(csv.DictReader(f))


class Facts:
    """Every number shown in the page text, with its exact value and source cell."""

    def __init__(self):
        self.items = {}

    def add(self, key, value, kind, src, doc=None, page=None, note=''):
        value = D(value)
        if kind == 'bn':      # USD millions -> "$47.5bn"
            shown = f'${rnd(value / 1000, 1)}bn'
        elif kind == 'bn2':
            shown = f'${rnd(value / 1000, 2)}bn'
        elif kind == 'bn0':
            shown = f'${rnd(value / 1000, 0)}bn'
        elif kind == 'm':     # USD millions -> "$649m"
            shown = f'${int(rnd(value, 0)):,}m'
        elif kind == 'pct':
            shown = f'{rnd(value, 1)}%'
        elif kind == 'pp':
            r = rnd(value, 1)
            shown = f'{"+" if r > 0 else "−"}{abs(r)} pp'
        elif kind == 'x1':
            shown = f'{rnd(value, 1)}'
        elif kind == 'x0':
            shown = f'{int(rnd(value, 0))}'
        else:
            raise ValueError(kind)
        self.items[key] = {'shown': shown, 'exact': str(value), 'kind': kind, 'source': src,
                           'doc': doc, 'page': page, 'note': note}
        return value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--research', required=True, type=Path)
    args = ap.parse_args()
    research = args.research.resolve()
    wb_dir = next((research / 'research/coreweave/stage5').glob('*/CoreWeave_RQ1_Debt_and_Leverage.xlsx')).parent.relative_to(research).as_posix()
    for k in INPUTS:
        INPUTS[k] = INPUTS[k].replace('{wb}', wb_dir)
    global WORKBOOK
    WORKBOOK = WORKBOOK.replace('{wb}', wb_dir)
    commit = subprocess.run(['git', '-C', str(research), 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()

    t = {k: read(v, research) for k, v in INPUTS.items()}
    F = Facts()

    # ---- documents and SEC links (workbook Sources sheet) ----
    import openpyxl
    wb = openpyxl.load_workbook(research / WORKBOOK)
    links = {}
    for r in wb['Sources'].iter_rows(min_row=5):
        if r[0].value and r[1].hyperlink:
            links[r[0].value] = {'url': r[1].hyperlink.target, 'filed': r[3].value, 'accession': r[4].value}
    docs = {}
    for sid, (name, short) in DOCS.items():
        info = links[name]
        assert info['url'].startswith('https://www.sec.gov/Archives/edgar/data/1769628/'), name
        docs[sid] = {'name': name, 'short': short, **info}
    evidence = {}
    for r in wb['Evidence Index'].iter_rows(min_row=4, values_only=True):
        if r[0] and r[1]:
            evidence[str(r[0])] = r[4]

    def cite(sid, page):
        return {'doc': sid, 'page': str(page)}

    dates = [{'iso': d, 'label': label(d), 'bs': cite(*BALANCE_SHEET[d])} for d in DATES]

    # ---- Exhibit 1: debt and leverage (note Figure 1) ----
    lev = {r['period_end']: r for r in t['leverage_table']}
    f1 = {}
    for r in t['fig1_debt_leverage']:
        f1.setdefault((r['figure'], r['series']), {})[r['period_end']] = r
    keyB, keyC = 'B = borrowings + finance leases', 'C = B + operating leases'
    ex1 = {'series': []}
    for key, name, sid in ((keyB, 'Headline Debt', 'headline'), (keyC, 'Lease-Inclusive Debt', 'lease')):
        ex1['series'].append({
            'id': sid, 'name': name,
            'usd_bn': [float(f1[('1a', key)][d]['plotted_value']) for d in DATES],
            'pct_assets': [float(f1[('1b', key)][d]['plotted_value']) for d in DATES],
            'hollow': [f1[('1a', key)][d]['marker'].startswith('hollow') for d in DATES],
        })
    for d in DATES:  # the figure CSV and the leverage table agree
        assert D(f1[('1a', keyB)][d]['source_value']) == D(lev[d]['B_headline'])
        assert D(f1[('1a', keyC)][d]['source_value']) == D(lev[d]['C_lease_inclusive'])
    ex1['borrowings_bn'] = [float(D(lev[d]['A_borrowings_carrying']) / 1000) for d in DATES]
    ex1['total_assets_bn'] = [float(D(lev[d]['total_assets']) / 1000) for d in DATES]

    LT = 'leverage_table.csv'
    BS26, BS23, BS24 = cite(*BALANCE_SHEET['2026-09-30']), cite('crwv-424b4-20250331', 'F-4, F-35'), cite('crwv-424b4-20250331', 'F-4, F-35')
    b23 = F.add('hd_2023', lev['2023-12-31']['B_headline'], 'bn', f'{LT} · 2023-12-31 · B_headline', **BS23)
    b26 = F.add('hd_2026', lev['2026-09-30']['B_headline'], 'bn', f'{LT} · 2026-09-30 · B_headline', **BS26)
    F.add('hd_multiple', b26 / b23, 'x0', f'{LT} · B_headline 2026-09-30 ÷ 2023-12-31', **BS26)
    F.add('borr_2023', lev['2023-12-31']['A_borrowings_carrying'], 'bn', f'{LT} · 2023-12-31 · A_borrowings_carrying', **BS23)
    F.add('borr_2026', lev['2026-09-30']['A_borrowings_carrying'], 'bn', f'{LT} · 2026-09-30 · A_borrowings_carrying', **BS26)
    F.add('lid_2023', lev['2023-12-31']['C_lease_inclusive'], 'bn', f'{LT} · 2023-12-31 · C_lease_inclusive', **BS23)
    F.add('lid_2026', lev['2026-09-30']['C_lease_inclusive'], 'bn', f'{LT} · 2026-09-30 · C_lease_inclusive', **BS26)
    F.add('opl_2023', lev['2023-12-31']['operating_leases'], 'm', f'{LT} · 2023-12-31 · operating_leases', **BS23)
    F.add('opl_2024', lev['2024-12-31']['operating_leases'], 'bn', f'{LT} · 2024-12-31 · operating_leases', **BS24)
    F.add('opl_2026', lev['2026-09-30']['operating_leases'], 'bn', f'{LT} · 2026-09-30 · operating_leases', **BS26)
    F.add('fin_2026', lev['2026-09-30']['finance_leases'], 'm', f'{LT} · 2026-09-30 · finance_leases', **BS26)
    assert D(lev['2026-09-30']['C_lease_inclusive']) - D(lev['2026-09-30']['B_headline']) == D(lev['2026-09-30']['operating_leases'])
    F.add('assets_2023', lev['2023-12-31']['total_assets'], 'bn', f'{LT} · 2023-12-31 · total_assets', **BS23)
    F.add('assets_2026', lev['2026-09-30']['total_assets'], 'bn', f'{LT} · 2026-09-30 · total_assets', **BS26)
    a23, a26 = D(lev['2023-12-31']['total_assets']), D(lev['2026-09-30']['total_assets'])
    F.add('assets_multiple', a26 / a23, 'x0', f'{LT} · total_assets 2026-09-30 ÷ 2023-12-31', **BS26)
    P = 'fig1_debt_leverage.csv (unrounded)'
    pct = {(k, d): D(f1[('1b', k)][d]['plotted_value']) for k in (keyB, keyC) for d in DATES}
    F.add('hd_pct_2023', pct[(keyB, '2023-12-31')], 'pct', f'{P} · 1b · B · 2023-12-31', **BS23)
    F.add('hd_pct_2024', pct[(keyB, '2024-12-31')], 'pct', f'{P} · 1b · B · 2024-12-31', **BS24)
    F.add('hd_pct_2026', pct[(keyB, '2026-09-30')], 'pct', f'{P} · 1b · B · 2026-09-30', **BS26)
    F.add('lid_pct_2023', pct[(keyC, '2023-12-31')], 'pct', f'{P} · 1b · C · 2023-12-31', **BS23)
    F.add('lid_pct_2024', pct[(keyC, '2024-12-31')], 'pct', f'{P} · 1b · C · 2024-12-31', **BS24)
    F.add('lid_pct_2026', pct[(keyC, '2026-09-30')], 'pct', f'{P} · 1b · C · 2026-09-30', **BS26)
    F.add('hd_pp_since24', pct[(keyB, '2026-09-30')] - pct[(keyB, '2024-12-31')], 'pp', f'{P} · B 2026-09-30 − 2024-12-31', **BS26)
    F.add('lid_pp_since24', pct[(keyC, '2026-09-30')] - pct[(keyC, '2024-12-31')], 'pp', f'{P} · C 2026-09-30 − 2024-12-31', **BS26)
    # third-quarter 2026 decomposition (an identity against end-of-period assets)
    B0, B1 = D(lev['2026-06-30']['B_headline']), D(lev['2026-09-30']['B_headline'])
    A0, A1 = D(lev['2026-06-30']['total_assets']), D(lev['2026-09-30']['total_assets'])
    debt_eff, asset_eff = (B1 - B0) / A1 * 100, (B0 / A1 - B0 / A0) * 100
    q2q3 = cite('crwv-10q-20261112', '6')
    F.add('q3_change', debt_eff + asset_eff, 'pp', f'{LT} · B and total_assets, 2026-06-30 and 2026-09-30', **q2q3)
    F.add('q3_debt_eff', debt_eff, 'pp', f'{LT} · (B 2026-09-30 − B 2026-06-30) ÷ assets 2026-09-30', **q2q3)
    F.add('q3_asset_eff', asset_eff, 'pp', f'{LT} · B 2026-06-30 × (1/assets 2026-09-30 − 1/assets 2026-06-30)', **q2q3)
    F.add('de_2026', D(lev['2026-09-30']['B_headline']) / D(lev['2026-09-30']['issuer_equity']), 'x1', f'{LT} · B_headline ÷ issuer_equity, 2026-09-30', **BS26)
    F.add('equity_2026', lev['2026-09-30']['issuer_equity'], 'bn', f'{LT} · 2026-09-30 · issuer_equity', **BS26)
    F.add('netdebt_2026', lev['2026-09-30']['net_debt_B'], 'bn', f'{LT} · 2026-09-30 · net_debt_B', **BS26)
    F.add('restricted_2026', lev['2026-09-30']['restricted_cash_total_not_deducted'], 'bn', f'{LT} · 2026-09-30 · restricted_cash_total_not_deducted', **BS26)
    F.add('recourse_2026', lev['2026-09-30']['recourse_carrying'], 'bn', f'{LT} · 2026-09-30 · recourse_carrying', **BS26)
    F.add('nonrec_2026', lev['2026-09-30']['nonrecourse_carrying'], 'bn', f'{LT} · 2026-09-30 · nonrecourse_carrying', **BS26)
    F.add('nonrec_2025', lev['2025-12-31']['nonrecourse_carrying'], 'bn', f'{LT} · 2025-12-31 · nonrecourse_carrying', doc='crwv-10q-20260812', page='6', note='December 2025 comparative column of the June 2026 10-Q')
    F.add('nonrec_share_2026', D(lev['2026-09-30']['nonrecourse_carrying']) / D(lev['2026-09-30']['A_borrowings_carrying']) * 100, 'pct', f'{LT} · nonrecourse_carrying ÷ A_borrowings_carrying, 2026-09-30', **BS26)

    # ---- Exhibit 2: layers (workbook Figure 4) ----
    fd = {}
    for r in t['figures_data']:
        fd.setdefault((r['figure'], r['series']), {})[WB_COL.get(r['column'], r['column'])] = r['value_usd_m']

    def wbseries(fig, series, ds=DATES):
        return [None if fd[(fig, series)].get(d, '') == '' else float(D(fd[(fig, series)][d]) / 1000) for d in ds]
    ex2 = {'series': [
        {'id': 'borrowings', 'name': 'Borrowings (carrying value)', 'usd_bn': wbseries('4', '(a) Borrowings (carrying value)')},
        {'id': 'finance', 'name': 'Finance-lease liabilities', 'usd_bn': wbseries('4', '(a) Finance lease liabilities')},
        {'id': 'operating', 'name': 'Operating-lease liabilities', 'usd_bn': wbseries('4', '(a) Operating lease liabilities')},
    ], 'total_bn': wbseries('4', '(a) Total above bar = Lease-Inclusive Debt')}
    for i, d in enumerate(DATES):  # layers add to Lease-Inclusive Debt and match the leverage table
        assert abs(sum(s['usd_bn'][i] for s in ex2['series']) - ex2['total_bn'][i]) < 1e-9
        assert D(fd[('4', '(a) Operating lease liabilities')][d]) == D(lev[d]['operating_leases'])

    # ---- Exhibit 3: instrument mix (note Figure 3) ----
    mixf = {}
    for r in t['fig2_instrument_mix']:
        mixf.setdefault(r['instrument_type'], {})[r['period_end']] = float(r['share_full_precision'])
    mixm = {}
    for r in t['instrument_mix']:
        mixm.setdefault(r['instrument_type'], {})[r['period_end']] = float(r['usd_millions'])
    ex3 = {'series': [{'id': f's{i}', 'name': k, 'share': [mixf[k][d] for d in DATES],
                       'usd_bn': [mixm[k][d] / 1000 for d in DATES]} for i, k in enumerate(TYPE_ORDER)]}
    lines_by_date = {}
    for r in t['instrument_lines']:
        lines_by_date.setdefault(r['period_end'], r)
    ex3['pages'] = {}
    for r in t['instrument_lines']:
        ex3['pages'].setdefault(r['period_end'], cite(r['source_id'], re.sub(r'^p\.? ?', '', r['locator'].replace('Note 10 debt table ', '').replace('p. ', ''))))
    for i, d in enumerate(DATES):
        assert abs(sum(s['share'][i] for s in ex3['series']) - 100) < 1e-9
    MX = 'instrument_mix.csv'
    debt_tbl26 = cite('crwv-10q-20261112', '30-31')
    mshare = {(r['instrument_type'], r['period_end']): D(r['share_full_precision']) for r in t['instrument_mix']}
    F.add('ddtl_share_2023', mshare[(TYPE_ORDER[0], '2023-12-31')], 'pct', f'{MX} · DDTL · 2023-12-31 · share_full_precision', doc='crwv-424b4-20250331', page='F-35')
    F.add('ddtl_share_2026', mshare[(TYPE_ORDER[0], '2026-09-30')], 'pct', f'{MX} · DDTL · 2026-09-30 · share_full_precision', **debt_tbl26)
    F.add('conv_share_2026', mshare[('Convertible notes', '2026-09-30')], 'pct', f'{MX} · Convertible notes · 2026-09-30', **debt_tbl26)
    F.add('senior_share_2026', mshare[('Senior notes', '2026-09-30')], 'pct', f'{MX} · Senior notes · 2026-09-30', **debt_tbl26)
    F.add('oem_share_2026', mshare[('OEM and software financing', '2026-09-30')], 'pct', f'{MX} · OEM and software financing · 2026-09-30', **debt_tbl26)
    F.add('ddtl_usd_2026', mixm[TYPE_ORDER[0]]['2026-09-30'], 'bn', f'{MX} · DDTL · 2026-09-30 · usd_millions', **debt_tbl26)
    F.add('ddtl_usd_2023', mixm[TYPE_ORDER[0]]['2023-12-31'], 'bn', f'{MX} · DDTL · 2023-12-31 · usd_millions', doc='crwv-424b4-20250331', page='F-35')
    principal26 = sum(D(r['usd_millions']) for r in t['instrument_mix'] if r['period_end'] == '2026-09-30')
    F.add('principal_2026', principal26, 'bn', f'{MX} · sum of usd_millions, 2026-09-30', **debt_tbl26)

    # ---- Exhibit 8: facility timeline (instrument lines, lanes) ----
    lanes = {}
    for r in t['instrument_lines']:
        lane = LANE[r['line_as_printed']]
        L = lanes.setdefault(lane, {'name': lane, 'type': r['instrument_type'], 'cells': {}})
        c = L['cells'].setdefault(r['period_end'], {'usd_m': 0.0, 'parts': []})
        v = float(r['usd_millions']) if r['usd_millions'] else 0.0
        c['usd_m'] += v
        c['parts'].append({'printed': r['line_as_printed'], 'section': r['recourse_section'],
                           'status': r['raw_status'], 'usd_m': v if r['usd_millions'] else None,
                           'doc': r['source_id'], 'page': re.sub(r'^p\.? ?', '', r['locator'].replace('Note 10 debt table ', '').replace('p. ', ''))})
    sec = {}
    for r in t['facility_security_timeline']:
        lvl = r['security_level']
        short = 'not restated' if lvl.startswith('pledged asset classes not separately restated') else lvl
        sec.setdefault(r['facility'], {})[r['as_of']] = {
            'security': short, 'security_page': r['security_page'], 'guarantee': r['guarantee_level'],
            'guarantee_page': r['guarantee_page'], 'doc': r['source_id']}
    order = {k: i for i, k in enumerate(TYPE_ORDER)}
    ex8 = []
    for lane in sorted(lanes.values(), key=lambda L: (order[L['type']], min(L['cells']), L['name'])):
        ex8.append({'name': lane['name'], 'type': lane['type'],
                    'cells': [None if d not in lane['cells'] or lane['cells'][d]['usd_m'] == 0 and all(p['usd_m'] is None for p in lane['cells'][d]['parts'])
                              else {'usd_m': round(lane['cells'][d]['usd_m'], 3), 'parts': lane['cells'][d]['parts']} for d in DATES],
                    'security': sec.get(lane['name'], {})})
    for i, d in enumerate(DATES):  # lanes add back to the principal total
        tot = sum((L['cells'][i] or {}).get('usd_m', 0) for L in ex8)
        assert abs(tot - sum(mixm[k][d] for k in TYPE_ORDER)) < 1e-6, d
    IL = 'instrument_lines.csv'
    lane_v = {L['name']: L['cells'] for L in ex8}
    F.add('ddtl20_2026', lane_v['DDTL 2.0'][8]['usd_m'], 'bn2', f'{IL} · DDTL 2.0 Facility · 2026-09-30', doc='crwv-10q-20261112', page='30')
    F.add('ddtl21_2026', lane_v['DDTL 2.1'][8]['usd_m'], 'bn2', f'{IL} · DDTL 2.1 Facility · 2026-09-30', doc='crwv-10q-20261112', page='30')
    F.add('ddtl40_2026', lane_v['DDTL 4.0'][8]['usd_m'], 'bn2', f'{IL} · DDTL 4.0 Facility · 2026-09-30', doc='crwv-10q-20261112', page='30')
    F.add('ddtl40_2026q1', lane_v['DDTL 4.0'][6]['usd_m'], 'bn2', f'{IL} · DDTL 4.0 Facility(1) · 2026-03-31', doc='crwv-10q-20260508', page='24')
    F.add('n_lanes_2026', sum(1 for L in ex8 if L['cells'][8] and L['cells'][8]['usd_m'] > 0), 'x0', f'{IL} · count of lines with principal at 2026-09-30', **debt_tbl26)
    F.add('n_lanes_2023', sum(1 for L in ex8 if L['cells'][0] and L['cells'][0]['usd_m'] > 0), 'x0', f'{IL} · count of lines with principal at 2023-12-31', doc='crwv-424b4-20250331', page='F-35')

    # ---- Exhibit 4: PP&E (note Figure 4) ----
    f3 = {}
    for r in t['fig3_ppe_composition']:
        f3.setdefault(r['group'], {})[r['period_end']] = D(r['usd_millions'])
    groups = list(f3)
    ex4 = {'series': [{'id': f'g{i}', 'name': g, 'usd_bn': [float(f3[g][d] / 1000) for d in DATES]} for i, g in enumerate(groups)]}
    ppe_pages = {}
    for r in t['ppe_categories']:
        ppe_pages.setdefault(r['period_end'], cite(r['source_id'], r['locator'].replace('Property and equipment note, p. ', '')))
    ex4['pages'] = ppe_pages
    gross = {d: sum(f3[g][d] for g in groups) for d in DATES}
    for d in DATES:
        assert gross[d] == D(fd[('5', 'Gross property and equipment')][d]), d
    tech, dc = groups[0], groups[1]
    PB = 'fig3_ppe_composition.csv'
    F.add('ppe_2023', gross['2023-12-31'], 'bn', f'{PB} · sum of groups · 2023-12-31', **ppe_pages['2023-12-31'])
    F.add('ppe_2026', gross['2026-09-30'], 'bn', f'{PB} · sum of groups · 2026-09-30', **ppe_pages['2026-09-30'])
    F.add('ppe_multiple', gross['2026-09-30'] / gross['2023-12-31'], 'x0', f'{PB} · gross 2026-09-30 ÷ 2023-12-31', **ppe_pages['2026-09-30'])
    F.add('tech_2023', f3[tech]['2023-12-31'], 'bn', f'{PB} · GPU proxy · 2023-12-31', **ppe_pages['2023-12-31'])
    F.add('tech_2026', f3[tech]['2026-09-30'], 'bn', f'{PB} · GPU proxy · 2026-09-30', **ppe_pages['2026-09-30'])
    for d, k in (('2023-12-31', 'tech_share_2023'), ('2024-12-31', 'tech_share_2024'), ('2025-12-31', 'tech_share_2025'), ('2026-09-30', 'tech_share_2026')):
        F.add(k, f3[tech][d] / gross[d] * 100, 'pct', f'{PB} · GPU proxy ÷ gross · {d}', **ppe_pages[d])
    F.add('dc_2026', f3[dc]['2026-09-30'], 'bn', f'{PB} · data-center group · 2026-09-30', **ppe_pages['2026-09-30'])
    F.add('ppe_d_2526', gross['2026-09-30'] - gross['2025-12-31'], 'bn', f'{PB} · gross 2026-09-30 − 2025-12-31', **ppe_pages['2026-09-30'])
    F.add('tech_d_2526', f3[tech]['2026-09-30'] - f3[tech]['2025-12-31'], 'bn', f'{PB} · GPU proxy 2026-09-30 − 2025-12-31', **ppe_pages['2026-09-30'])
    F.add('dc_d_2526', f3[dc]['2026-09-30'] - f3[dc]['2025-12-31'], 'bn', f'{PB} · data-center group 2026-09-30 − 2025-12-31', **ppe_pages['2026-09-30'])
    F.add('tech_d_q3', f3[tech]['2026-09-30'] - f3[tech]['2026-06-30'], 'bn', f'{PB} · GPU proxy 2026-09-30 − 2026-06-30', **ppe_pages['2026-09-30'])
    cip = {r['as_of']: D(r['amount_1_usd_m']) for r in t['routes_dated'] if r['measure'] == 'Construction in progress'}
    F.add('cip_d_q3', cip['2026-06-30'] - cip['2026-09-30'], 'bn', 'routes_dated.csv · Construction in progress 2026-06-30 − 2026-09-30 (a fall)', **ppe_pages['2026-09-30'])
    F.add('tech_minus_hd', D(lev['2026-09-30']['B_headline']) - f3[tech]['2026-09-30'], 'm', f'{LT} B_headline − {PB} GPU proxy, 2026-09-30', **BS26)

    # ---- Exhibit 5: debt beside PP&E (workbook Figure 5) ----
    ex5 = {'series': [
        {'id': 'headline', 'name': 'Headline Debt', 'usd_bn': wbseries('5', 'Headline Debt (borrowings + finance leases)')},
        {'id': 'gross', 'name': 'Gross property and equipment', 'usd_bn': wbseries('5', 'Gross property and equipment')},
        {'id': 'tech', 'name': 'Technology equipment (GPU proxy)', 'usd_bn': wbseries('5', 'Technology equipment, gross (our GPU proxy)')},
    ]}

    # ---- Exhibit 6: leases on and off the balance sheet (workbook Figure 7) ----
    ex6 = {'series': [
        {'id': 'operating', 'name': 'Operating-lease liabilities (present value, on the balance sheet)', 'usd_bn': wbseries('7', 'Operating lease liabilities on the balance sheet (present value)')},
        {'id': 'signed', 'name': 'Signed leases not yet commenced (undiscounted, as estimated)', 'usd_bn': wbseries('7', 'Estimated undiscounted payments on signed leases awaiting commencement, as reported')},
    ], 'signed_pages': {}}
    est = 'Estimated future undiscounted lease payments at the balance'
    for r in t['routes_dated']:
        if r['route_or_pool'] == 'Leased, signed but not yet commenced' and r['measure'].startswith(est):
            ex6['signed_pages'][r['as_of']] = cite(r['source_id'], r['printed_page'])
            assert D(r['amount_1_usd_m']) == D(fd[('7', 'Estimated undiscounted payments on signed leases awaiting commencement, as reported')][r['as_of']])
    signed = {d: D(fd[('7', 'Estimated undiscounted payments on signed leases awaiting commencement, as reported')][d]) for d in DATES[1:]}
    F.add('signed_2024', signed['2024-12-31'], 'bn', 'routes_dated.csv · signed not commenced · 2024-12-31', **ex6['signed_pages']['2024-12-31'])
    F.add('signed_2026', signed['2026-09-30'], 'bn', 'routes_dated.csv · signed not commenced · 2026-09-30', **ex6['signed_pages']['2026-09-30'])
    excl = [r for r in t['routes_dated'] if r['as_of'] == '2026-09-30' and r['measure'].startswith('Excluded lease')][0]
    F.add('excluded_ceiling_2026', excl['amount_1_usd_m'], 'bn', 'routes_dated.csv · excluded lease contractual maximum · 2026-09-30', **cite(excl['source_id'], excl['printed_page']))
    rou = {r['as_of']: D(r['amount_1_usd_m']) for r in t['routes_dated'] if r['measure'].startswith('Operating lease right-of-use')}
    F.add('rou_2026', rou['2026-09-30'], 'bn', 'routes_dated.csv · operating-lease ROU assets · 2026-09-30', **BS26)

    # ---- Exhibit 7: sources and uses (workbook Figure 6) ----
    su = {}
    for r in t['sources_uses']:
        su[(r['period'], r['line'])] = r
    lines7 = [('Cash from operations', 'Cash from operations'), ('Proceeds from issuance of debt, net', "Debt issued, net (issuer's caption)"),
              ('Equity: IPO proceeds', 'Equity: IPO'), ('Equity: private placements', 'Equity: private placements'),
              ('Repayments of debt', 'Debt repaid'), ('Purchases of property and equipment (cash capex)', 'Cash capex'),
              ('Capped calls', 'Capped calls'), ('Investments in unconsolidated JV and VIEs', 'Joint venture / VIE investments')]
    ex7 = {'periods': ['9M 2025', '9M 2026'], 'rows': []}
    wbmap = {'Cash from operations': 'Cash From Operations', "Debt issued, net (issuer's caption)": None}
    for line, name in lines7:
        vals = []
        for p in ('9M2025', '9M2026'):
            r = su[(p, line)]
            vals.append(None if r['contribution_usd_millions'] == '' else float(D(r['contribution_usd_millions']) / 1000))
        ex7['rows'].append({'name': name, 'usd_bn': vals, 'printed': [su[(p, line)]['raw_status'] for p in ('9M2025', '9M2026')]})
    resid = [r for r in t['sources_uses'] if r['role'] == 'residual']
    ex7['rows'].append({'name': 'All other flows (calculated residual)', 'usd_bn': [float(D(next(r['usd_millions'] for r in resid if r['period'] == p)) / 1000) for p in ('9M2025', '9M2026')], 'printed': ['calculated', 'calculated']})
    ex7['rows'].append({'name': 'Change in cash and restricted cash', 'total': True, 'usd_bn': [float(D(su[(p, 'Net change in cash, cash equivalents and restricted cash')]['usd_millions']) / 1000) for p in ('9M2025', '9M2026')], 'printed': ['disclosed', 'disclosed']})
    # the bars match the workbook figure data and add to the change in cash
    wbrows = ['Cash From Operations', "Debt Issued, Net (Issuer's Caption)", 'Equity: IPO', 'Equity: Private Placements', 'Debt Repaid',
              'Cash Capex (Purchases of Property and Equipment)', 'Capped Calls', 'Joint Venture / VIE Investments', 'All Other Flows (Residual)',
              'Change in Cash, Cash Equivalents and Restricted Cash']
    fig6 = {(r['series'][-4:], r['row_label']): D(r['value_usd_m']) for r in t['figures_data'] if r['figure'] == '6'}
    for j, p in enumerate(('2025', '2026')):
        for row, wbname in zip(ex7['rows'], wbrows):
            assert D(str(row['usd_bn'][j] or 0)) * 1000 == fig6[(p, wbname)], (p, wbname)
        assert abs(sum(r['usd_bn'][j] or 0 for r in ex7['rows'][:-1]) - ex7['rows'][-1]['usd_bn'][j]) < 1e-9
    CF = cite('crwv-10q-20261112', '12')
    SU = 'sources_uses.csv'

    def suv(p, line):
        return D(su[(p, line)]['usd_millions'])
    F.add('cfo_9m26', suv('9M2026', 'Cash from operations'), 'bn', f'{SU} · 9M2026 · Cash from operations', **CF)
    F.add('cfo_9m25', suv('9M2025', 'Cash from operations'), 'bn', f'{SU} · 9M2025 · Cash from operations', **CF)
    F.add('defrev_9m26', suv('9M2026', 'of which: net change in deferred revenue (already inside operating cash flow)'), 'bn', f'{SU} · 9M2026 · deferred revenue memo', **CF)
    di, dr = suv('9M2026', 'Proceeds from issuance of debt, net'), suv('9M2026', 'Repayments of debt')
    F.add('debtiss_9m26', di, 'bn', f'{SU} · 9M2026 · Proceeds from issuance of debt, net', **CF)
    F.add('debtiss_9m25', suv('9M2025', 'Proceeds from issuance of debt, net'), 'bn', f'{SU} · 9M2025 · Proceeds from issuance of debt, net', **CF)
    F.add('debtrep_9m26', -dr, 'bn', f'{SU} · 9M2026 · Repayments of debt (shown as a positive amount)', **CF)
    F.add('netborrow_9m26', di + dr, 'bn', f'{SU} · 9M2026 · debt issued + debt repaid', **CF)
    F.add('netborrow_over_cfo', (di + dr) / suv('9M2026', 'Cash from operations'), 'x1', f'{SU} · 9M2026 · (debt issued + repaid) ÷ cash from operations', **CF)
    F.add('capex_9m26', -suv('9M2026', 'Purchases of property and equipment (cash capex)'), 'bn', f'{SU} · 9M2026 · cash capex (shown as a positive amount)', **CF)
    F.add('capex_9m25', -suv('9M2025', 'Purchases of property and equipment (cash capex)'), 'bn', f'{SU} · 9M2025 · cash capex (shown as a positive amount)', **CF)
    F.add('capex_multiple', suv('9M2026', 'Purchases of property and equipment (cash capex)') / suv('9M2025', 'Purchases of property and equipment (cash capex)'), 'x1', f'{SU} · cash capex 9M2026 ÷ 9M2025', **CF)
    F.add('privplace_9m26', suv('9M2026', 'Equity: private placements'), 'bn', f'{SU} · 9M2026 · Equity: private placements', **CF)
    F.add('cappedcalls_9m26', -suv('9M2026', 'Capped calls'), 'bn', f'{SU} · 9M2026 · Capped calls (shown as a positive amount)', **CF)
    F.add('ppeliab_9m26', suv('9M2026', 'Liabilities related to PP&E additions (issuer label; includes OEM-financed additions and unpaid capitalized interest)') if ('9M2026', 'Liabilities related to PP&E additions (issuer label; includes OEM-financed additions and unpaid capitalized interest)') in su else next(D(r['usd_millions']) for r in t['sources_uses'] if r['period'] == '9M2026' and r['line'].startswith('Liabilities related to PP&E')), 'bn', f'{SU} · 9M2026 · non-cash: liabilities related to PP&E additions', **CF)
    F.add('rouacq_9m26', next(D(r['usd_millions']) for r in t['sources_uses'] if r['period'] == '9M2026' and r['line'].startswith('Operating-lease ROU')), 'bn', f'{SU} · 9M2026 · non-cash: operating-lease ROU assets acquired', **CF)

    # ---- Exhibit 9: collateral and recourse (workbook Figure 8) ----
    col = {}
    for r in t['collateral_dated']:
        if r['amount_1_usd_m']:
            col.setdefault(r['route_or_pool'], {})[r['as_of']] = (D(r['amount_1_usd_m']), D(r['amount_2_usd_m']), cite(r['source_id'], r['printed_page']))
    spv_key = next(k for k in col if k.startswith('Certain special-purpose'))
    ccac = col['CCAC VIII (DDTL 4.0)']
    cdates = ['2025-12-31', '2026-06-30', '2026-09-30']
    ex9 = {'dates': [label(d) for d in cdates], 'pools': [
        {'id': 'spv', 'name': 'Certain special-purpose subsidiaries (aggregate, not named)',
         'noncurrent_bn': [float(col[spv_key][d][0] / 1000) for d in cdates], 'current_bn': [float(col[spv_key][d][1] / 1000) for d in cdates],
         'cite': [col[spv_key][d][2] for d in cdates]},
        {'id': 'ccac', 'name': 'CCAC VIII, the DDTL 4.0 borrower',
         'noncurrent_bn': [None] + [float(ccac[d][0] / 1000) for d in cdates[1:]], 'current_bn': [None] + [float(ccac[d][1] / 1000) for d in cdates[1:]],
         'cite': [None] + [ccac[d][2] for d in cdates[1:]]}],
        'recourse_bn': [float(D(lev[d]['recourse_carrying']) / 1000) for d in cdates],
        'nonrecourse_bn': [float(D(lev[d]['nonrecourse_carrying']) / 1000) for d in cdates],
        'recourse_cite': [cite('crwv-10q-20260812', '6'), cite('crwv-10q-20260812', '6'), cite('crwv-10q-20261112', '6')]}
    for d in cdates[1:]:
        assert col[spv_key][d][0] == D(fd[('8', '(a) Special-purpose subsidiaries: non-current')][d])
    CD = 'collateral_dated.csv'
    for d, k in (('2025-12-31', '2025'), ('2026-06-30', '2026q2'), ('2026-09-30', '2026')):
        F.add(f'spv_nc_{k}', col[spv_key][d][0], 'bn', f'{CD} · special-purpose subsidiaries · {d} · non-current', **col[spv_key][d][2])
        F.add(f'spv_c_{k}', col[spv_key][d][1], 'bn', f'{CD} · special-purpose subsidiaries · {d} · current', **col[spv_key][d][2])
    F.add('ccac_nc_2026', ccac['2026-09-30'][0], 'bn', f'{CD} · CCAC VIII · 2026-09-30 · non-current', **ccac['2026-09-30'][2])
    F.add('ccac_c_2026', ccac['2026-09-30'][1], 'm', f'{CD} · CCAC VIII · 2026-09-30 · current', **ccac['2026-09-30'][2])

    # ---- Evidence ladder: OEM, notes ----
    o = [r for r in t['oem_case'] if r['measure'] == 'Outstanding OEM equipment financing' and r['as_of'] == '2025-12-31'][0]
    F.add('oem_2024', o['amount_2_usd_m'], 'bn', 'oem_case.csv · Outstanding OEM equipment financing · 2025-12-31 row · amount_2 (Dec 2024)', doc=o['source_id'], page=o['printed_page'])
    F.add('oem_2025', o['amount_1_usd_m'], 'bn', 'oem_case.csv · Outstanding OEM equipment financing · 2025-12-31 row · amount_1', doc=o['source_id'], page=o['printed_page'])
    o26 = [r for r in t['oem_case'] if r['measure'] == 'Outstanding OEM equipment financing' and r['as_of'] == '2026-09-30'][0]
    F.add('oem_2026', o26['amount_1_usd_m'], 'bn', 'oem_case.csv · Outstanding OEM equipment financing · 2026-09-30', doc=o26['source_id'], page=o26['printed_page'])
    sw = [r for r in t['oem_case'] if r['measure'] == 'Outstanding software-licence financing'][0]
    F.add('software_2026', sw['amount_1_usd_m'], 'm', 'oem_case.csv · Outstanding software-licence financing · 2026-09-30', doc=sw['source_id'], page=sw['printed_page'])
    oem_quotes = {r['as_of'] + ' · ' + r['measure']: {'text': r['text_as_printed'], 'doc': r['source_id'], 'page': r['printed_page']} for r in t['oem_case']}
    notes = [{'issue': r['route_or_pool'], 'what': r['kind'], 'usd_m': r['amount_1_usd_m'] or None, 'usd_m_2': r['amount_2_usd_m'] or None,
              'doc': r['source_id'], 'page': r['printed_page']} for r in t['note_issue_uses']]
    NU = 'note_issue_uses.csv'
    for r in t['note_issue_uses']:
        if r['amount_1_usd_m'] and 'Convertible Senior' in r['route_or_pool']:
            F.add('capped_' + r['route_or_pool'][:4], r['amount_1_usd_m'], 'm', f'{NU} · {r["route_or_pool"]} · capped-call cost', doc=r['source_id'], page=r['printed_page'])
        if r['amount_1_usd_m'] and 'Promissory' in r['route_or_pool']:
            F.add('promissory_face', r['amount_1_usd_m'], 'm', f'{NU} · Convertible Promissory Notes · face', doc=r['source_id'], page='118')
            F.add('promissory_fv', r['amount_2_usd_m'], 'm', f'{NU} · Convertible Promissory Notes · fair value', doc=r['source_id'], page='107')
    cases = {}
    for r in t['facility_cases']:
        cases.setdefault(r['facility'], []).append({'entry': r['entry'], 'text': r['what_the_document_says'], 'document': r['document'],
                                                    'where': ' '.join(r['where_to_look'].split()), 'docs': [s.strip() for s in r['source_id'].split(';')]})

    # ---- cross-check against the workbook Evidence Index exact values ----
    xref = {'hd_2023': '1.04', 'hd_2026': '1.03', 'borr_2023': '1.01', 'borr_2026': '1.02', 'lid_2023': '1.06', 'lid_2026': '1.05',
            'opl_2024': '1.07', 'opl_2026': '1.08', 'hd_pct_2023': '1.09', 'hd_pct_2024': '1.10', 'hd_pct_2026': '1.11',
            'lid_pct_2023': '1.12', 'lid_pct_2024': '1.13', 'lid_pct_2026': '1.14', 'hd_pp_since24': '1.15', 'lid_pp_since24': '1.16',
            'q3_change': '1.17', 'q3_debt_eff': '1.18', 'q3_asset_eff': '1.19', 'de_2026': '1.20', 'netdebt_2026': '1.21',
            'restricted_2026': '1.22', 'nonrec_2025': '1.23', 'nonrec_2026': '1.24', 'recourse_2026': '1.25', 'fin_2026': '1.39',
            'signed_2026': '1.29', 'excluded_ceiling_2026': '1.32', 'ddtl_share_2023': '1.33', 'ddtl_share_2026': '1.34',
            'conv_share_2026': '1.35', 'senior_share_2026': '1.36', 'oem_share_2026': '1.37', 'ddtl_usd_2026': '1.38',
            'ppe_2023': '2.01', 'ppe_2026': '2.02', 'tech_share_2023': '2.03', 'tech_share_2024': '2.04', 'tech_share_2025': '2.05',
            'tech_share_2026': '2.06', 'ppe_d_2526': '2.10', 'tech_d_2526': '2.11', 'dc_d_2526': '2.12', 'tech_d_q3': '2.14',
            'capex_9m25': '2.15', 'capex_9m26': '2.16', 'debtiss_9m26': '2.17', 'cfo_9m26': '2.18', 'defrev_9m26': '2.19',
            'ppeliab_9m26': '2.20', 'rouacq_9m26': '2.21', 'debtrep_9m26': '2.22', 'netborrow_9m26': '2.25', 'netborrow_over_cfo': '2.26',
            'ddtl20_2026': '3.01', 'ddtl21_2026': '3.02', 'ddtl40_2026': '3.03', 'ddtl40_2026q1': '3.04', 'oem_2024': '3.13',
            'oem_2025': '3.14', 'oem_2026': '3.15', 'software_2026': '3.16', 'promissory_face': '3.17', 'promissory_fv': '3.18',
            'capped_2031': '3.19', 'capped_2032': '3.20', 'capped_2033': '3.21', 'cip_d_q3': '2.13'}
    for key, ref in xref.items():
        ev = D(str(evidence[ref]))
        mine = D(F.items[key]['exact'])
        if key in ('capex_9m25', 'capex_9m26', 'debtrep_9m26', 'cip_d_q3'):
            ev = abs(ev)
        assert abs(mine - ev) < D('0.0000001'), (key, ref, mine, ev)
        F.items[key]['evidence_ref'] = ref

    data = {
        'company': 'CoreWeave, Inc.', 'generated': date.today().isoformat(),
        'research_commit': commit, 'dates': dates, 'docs': docs,
        'ex1': ex1, 'ex2': ex2, 'ex3': ex3, 'ex4': ex4, 'ex5': ex5, 'ex6': ex6, 'ex7': ex7, 'ex8': ex8, 'ex9': ex9,
        'cases': cases, 'oem': oem_quotes, 'notes': notes,
        'facts': F.items,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'data.json').write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')

    # numbers.csv: every displayed number with its source
    with open(OUT / 'numbers.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['key', 'shown', 'exact_value', 'source_csv_and_cell', 'evidence_index_ref', 'filing', 'printed_page', 'sec_url', 'note'])
        for k, v in F.items.items():
            d = docs.get(v['doc'], {})
            w.writerow([k, v['shown'], v['exact'], v['source'], v.get('evidence_ref', ''), d.get('name', ''), v['page'] or '', d.get('url', ''), v['note']])

    # exhibit CSVs: plotted values with their filing and page
    def write(name, header, rows):
        with open(OUT / name, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
    H = ['exhibit', 'series', 'period_end', 'value', 'unit', 'filing', 'printed_page', 'sec_url', 'source_file']

    def drow(ex, s, d, v, unit, c, srcfile):
        doc = docs[c['doc']] if c else {}
        return [ex, s, d, '' if v is None else v, unit, doc.get('name', ''), c['page'] if c else '', doc.get('url', ''), srcfile]
    rows = []
    for s in ex1['series']:
        for i, d in enumerate(DATES):
            rows.append(drow(1, s['name'], d, s['usd_bn'][i], 'USD billions', dates[i]['bs'], 'fig1_debt_leverage.csv'))
            rows.append(drow(1, s['name'] + ' / total assets', d, s['pct_assets'][i], 'percent', dates[i]['bs'], 'fig1_debt_leverage.csv'))
    write('exhibit-1-debt-leverage.csv', H, rows)
    rows = [drow(2, s['name'], d, s['usd_bn'][i], 'USD billions', dates[i]['bs'], 'figures_data.csv (workbook Figure 4)') for s in ex2['series'] for i, d in enumerate(DATES)]
    write('exhibit-2-debt-layers.csv', H, rows)
    rows = [drow(3, s['name'], d, s['share'][i], 'percent of listed principal', ex3['pages'][d], 'fig2_instrument_mix.csv') for s in ex3['series'] for i, d in enumerate(DATES)]
    write('exhibit-3-instrument-mix.csv', H, rows)
    rows = [drow(4, s['name'], d, s['usd_bn'][i], 'USD billions (gross)', ppe_pages[d], 'fig3_ppe_composition.csv') for s in ex4['series'] for i, d in enumerate(DATES)]
    write('exhibit-4-ppe-composition.csv', H, rows)
    rows = []
    for s in ex5['series']:
        for i, d in enumerate(DATES):
            rows.append(drow(5, s['name'], d, s['usd_bn'][i], 'USD billions', dates[i]['bs'] if s['id'] == 'headline' else ppe_pages[d], 'figures_data.csv (workbook Figure 5)'))
    write('exhibit-5-debt-and-equipment.csv', H, rows)
    rows = []
    for i, d in enumerate(DATES):
        rows.append(drow(6, ex6['series'][0]['name'], d, ex6['series'][0]['usd_bn'][i], 'USD billions', dates[i]['bs'], 'figures_data.csv (workbook Figure 7)'))
        rows.append(drow(6, ex6['series'][1]['name'], d, ex6['series'][1]['usd_bn'][i], 'USD billions (n.d. where blank)', ex6['signed_pages'].get(d), 'figures_data.csv (workbook Figure 7)'))
    write('exhibit-6-leases.csv', H, rows)
    rows = [drow(7, r['name'], p, r['usd_bn'][j], 'USD billions, signs as printed', CF, 'sources_uses.csv') for r in ex7['rows'] for j, p in enumerate(['9M 2025', '9M 2026'])]
    write('exhibit-7-sources-uses.csv', H, rows)
    rows = []
    for L in ex8:
        for i, d in enumerate(DATES):
            c = L['cells'][i]
            if c:
                for p in c['parts']:
                    rows.append([8, f"{L['name']} ({p['printed']}; {p['section']})", d, '' if p['usd_m'] is None else p['usd_m'],
                                 'USD millions, listed principal' + (' (printed dash)' if p['status'] == 'printed_dash' else ''),
                                 docs[p['doc']]['name'], p['page'], docs[p['doc']]['url'], 'instrument_lines.csv'])
    write('exhibit-8-facility-timeline.csv', H, rows)
    rows = []
    for pool in ex9['pools']:
        for i, d in enumerate(cdates):
            for part in ('noncurrent', 'current'):
                rows.append(drow(9, f"{pool['name']}: {part}", d, pool[f'{part}_bn'][i], 'USD billions', pool['cite'][i], 'collateral_dated.csv'))
    for i, d in enumerate(cdates):
        rows.append(drow(9, 'Recourse debt (carrying value)', d, ex9['recourse_bn'][i], 'USD billions', ex9['recourse_cite'][i], 'leverage_table.csv'))
        rows.append(drow(9, 'Non-recourse debt (carrying value)', d, ex9['nonrecourse_bn'][i], 'USD billions', ex9['recourse_cite'][i], 'leverage_table.csv'))
    write('exhibit-9-collateral.csv', H, rows)

    prov = {'research_repository': 'nicholasberoud/ai-compute-economics (private)', 'research_commit': commit,
            'generated': date.today().isoformat(), 'script': 'scripts/neocloud/extract_coreweave.py',
            'inputs': {Path(INPUTS[k]).name: hashlib.sha256((research / INPUTS[k]).read_bytes()).hexdigest() for k in INPUTS},
            'workbook_read_for_links_and_pages_only': {Path(WORKBOOK).name: hashlib.sha256((research / WORKBOOK).read_bytes()).hexdigest()},
            'cross_checked_against_evidence_index': len(xref), 'numbers': len(F.items)}
    (OUT / 'provenance.json').write_text(json.dumps(prov, indent=1) + '\n')
    print(f'wrote {OUT.relative_to(ROOT)}: {len(F.items)} numbers, {len(xref)} cross-checked against the Evidence Index')


if __name__ == '__main__':
    main()
