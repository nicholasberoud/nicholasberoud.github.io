"""Render the neocloud financing page and its homepage and Projects entries.

Reads assets/neocloud-2026-11/coreweave/data.json (written by
extract_coreweave.py) and scripts/neocloud/coreweave.template.html, and writes:

  projects/ai-infrastructure-financing.html   the study page
  index.html, research.html                   the project card and list entry, between neocloud markers
  scripts/neocloud/CHECKLIST-coreweave.md     every displayed number tied to its source (not deployed)

Every {{key}} in the template must name a number in data.json; the build
fails on an unknown key, an unfilled placeholder or an em dash in the prose.
Usage: python3 scripts/neocloud/render_page.py
"""
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'assets/neocloud-2026-11/coreweave/data.json'
TEMPLATE = ROOT / 'scripts/neocloud/coreweave.template.html'
PAGE = ROOT / 'projects/ai-infrastructure-financing.html'
CHECKLIST = ROOT / 'scripts/neocloud/CHECKLIST-coreweave.md'

d = json.loads(DATA.read_text())
F, docs, dates = d['facts'], d['docs'], d['dates']
used = {}


def fact(key, plain=False, where='page'):
    if key not in F:
        raise KeyError(f'unknown number {key!r} in {where}')
    used.setdefault(key, set()).add(where)
    f = F[key]
    if plain:
        return f['shown']
    doc = docs.get(f['doc'])
    title = f"{doc['short']}, p. {f['page']}" if doc else ''
    return f'<span class="nc-fact" title="Source: {html.escape(title)}">{html.escape(f["shown"])}</span>'


def fill(text, where):
    return re.sub(r'\{\{([a-z0-9_]+)(\|plain)?\}\}', lambda m: fact(m.group(1), bool(m.group(2)), where), text)


def link(c):
    doc = docs[c['doc']]
    return f'<a href="{doc["url"]}">{html.escape(doc["short"])}</a>'


def sources(cites):
    """Group (doc, page) citations by document, in first-seen order."""
    order, pages = [], {}
    for c in cites:
        if not c:
            continue
        if c['doc'] not in pages:
            order.append(c['doc'])
            pages[c['doc']] = []
        for p in str(c['page']).split(', '):
            if p not in pages[c['doc']]:
                pages[c['doc']].append(p)
    return '; '.join(f'{link({"doc": k})} p. {", ".join(pages[k])}' for k in order)


def bn(v, places=1):
    if v is None:
        return 'n.d.'
    return f'{"−" if v < 0 else ""}{abs(v):,.{places}f}'


def table(caption, head, rows):
    h = ''.join(f'<th scope="col">{html.escape(x)}</th>' for x in head)
    b = ''.join('<tr>' + f'<th scope="row">{html.escape(r[0])}</th>' + ''.join(f'<td>{x}</td>' for x in r[1:]) + '</tr>' for r in rows)
    return (f'<details class="nc-table"><summary>Data table</summary><div class="table-wrap" tabindex="0">'
            f'<table class="data-table"><caption>{html.escape(caption)}</caption><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div></details>')


L = [x['label'] for x in dates]
e1, e2, e3, e4, e5, e6, e7, e8, e9 = (d[f'ex{i}'] for i in range(1, 10))
TABLES = {
    'ex1': table('USD billions and percent of total assets', ['Date', 'Headline Debt', '% of assets', 'Lease-Inclusive Debt', '% of assets', 'Total assets'],
                 [[L[i], bn(e1['series'][0]['usd_bn'][i]), f"{e1['series'][0]['pct_assets'][i]:.1f}", bn(e1['series'][1]['usd_bn'][i]), f"{e1['series'][1]['pct_assets'][i]:.1f}", bn(e1['total_assets_bn'][i])] for i in range(9)]),
    'ex2': table('USD billions', ['Date', 'Borrowings', 'Finance leases', 'Operating leases', 'Lease-Inclusive Debt'],
                 [[L[i]] + [bn(s['usd_bn'][i], 3) for s in e2['series']] + [bn(e2['total_bn'][i], 3)] for i in range(9)]),
    'ex6': table('USD billions; n.d. = not disclosed', ['Date', 'Operating-lease liabilities (present value)', 'Signed, not commenced (undiscounted)'],
                 [[L[i], bn(e6['series'][0]['usd_bn'][i], 3), bn(e6['series'][1]['usd_bn'][i])] for i in range(9)]),
    'ex3': table('Percent of listed principal', ['Instrument'] + L, [[s['name']] + [f"{v:.2f}" for v in s['share']] for s in e3['series']]),
    'ex8': table('Listed principal, USD millions; blank = not listed or printed as a dash', ['Debt line'] + L,
                 [[x['name']] + ['' if c is None else f"{c['usd_m']:,.0f}" for c in x['cells']] for x in e8]),
    'ex4': table('USD billions, gross', ['Date', 'Technology equipment', 'Data-center group', 'Other', 'Gross PP&E', 'Technology share'],
                 [[L[i]] + [bn(s['usd_bn'][i], 3) for s in e4['series']] + [bn(sum(s['usd_bn'][i] for s in e4['series']), 3), f"{e4['series'][0]['usd_bn'][i] / sum(s['usd_bn'][i] for s in e4['series']) * 100:.1f}%"] for i in range(9)]),
    'ex5': table('USD billions', ['Date'] + [s['name'] for s in e5['series']], [[L[i]] + [bn(s['usd_bn'][i], 3) for s in e5['series']] for i in range(9)]),
    'ex7': table('USD billions, signs as printed; “no line” = no separate line that period', ['Line', '9M 2025', '9M 2026'],
                 [[r['name']] + ['no line' if v is None else bn(v, 3) for v in r['usd_bn']] for r in e7['rows']]),
    'ex9': table('USD billions; n/a = DDTL 4.0 not yet signed', ['Measure'] + e9['dates'],
                 [[f"{p['name']}: {part}"] + ['n/a' if v is None else bn(v, 3) for v in p[f'{part}_bn']] for p in e9['pools'] for part in ('noncurrent', 'current')]
                 + [['Recourse debt'] + [bn(v, 3) for v in e9['recourse_bn']], ['Non-recourse debt'] + [bn(v, 3) for v in e9['nonrecourse_bn']]]),
}
bs = [x['bs'] for x in dates]
lane_cites = [{'doc': p['doc'], 'page': p['page']} for x in e8 for c in x['cells'] if c for p in c['parts']]
SRC = {
    'ex1': sources(bs), 'ex2': sources(bs), 'ex6': sources(bs + [e6['signed_pages'].get(x['iso']) for x in dates]),
    'ex3': sources([e3['pages'][x['iso']] for x in dates]), 'ex8': sources(lane_cites),
    'ex4': sources([e4['pages'][x['iso']] for x in dates]), 'ex5': sources(bs + [e4['pages'][x['iso']] for x in dates]),
    'ex7': sources([{'doc': 'crwv-10q-20261112', 'page': '12'}]) + ' (consolidated statements of cash flows, both nine-month columns)',
    'ex9': sources(e9['pools'][0]['cite'] + e9['pools'][1]['cite'] + e9['recourse_cite']),
}
DOCS = ('<div class="table-wrap" tabindex="0"><table class="data-table data-table--text nc-docs"><thead><tr><th scope="col">Document</th><th scope="col">Filed</th><th scope="col">SEC accession</th></tr></thead><tbody>'
        + ''.join(f'<tr><th scope="row"><a href="{v["url"]}">{html.escape(v["name"])}</a></th><td>{html.escape(str(v["filed"]))}</td><td>{html.escape(str(v["accession"]))}</td></tr>' for v in docs.values())
        + '</tbody></table></div>')

# chart payload: everything the script draws, nothing more
payload = {k: d[k] for k in ('dates', 'docs', 'ex1', 'ex2', 'ex3', 'ex4', 'ex5', 'ex6', 'ex7', 'ex8', 'ex9')}
payload['docs'] = {k: {'short': v['short'], 'url': v['url']} for k, v in docs.items()}
data_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

src = TEMPLATE.read_text()
version = hashlib.sha256((src + data_json + (ROOT / 'assets/neocloud-2026-11/neocloud.js').read_text() + (ROOT / 'assets/neocloud-2026-11/neocloud.css').read_text()).encode()).hexdigest()[:10]
n_xref = sum(1 for f in F.values() if f.get('evidence_ref'))
out = src.replace('{{DATA}}', data_json).replace('{{DOCS}}', DOCS).replace('{{VERSION}}', version)
out = re.sub(r'\{\{TABLE (ex\d)\}\}', lambda m: TABLES[m.group(1)], out)
out = re.sub(r'\{\{SRC (ex\d)\}\}', lambda m: SRC[m.group(1)], out)
out = fill(out, 'page')
out = out.replace('{{N_FACTS}}', str(len(used)))
out = out.replace('{{N_XREF_SENTENCE}}', f'. {sum(1 for k in used if F[k].get("evidence_ref"))} of them were also matched exactly against the research workbook’s evidence index.')
leftover = re.findall(r'\{\{[^}]*\}\}', out)
assert not leftover, leftover
prose = re.sub(r'<script.*?</script>', '', out, flags=re.S)
assert '—' not in prose, 'em dash in page prose'
PAGE.write_text(out)

# ---- homepage card and Projects entry ----
CARD = '''<!-- neocloud-card:start (generated by scripts/neocloud/render_page.py) -->
<article class="treasury-feature" id="ai-infrastructure" aria-labelledby="ai-feature-heading">
<div class="treasury-feature-body">
<p class="eyebrow">Research assistant work · CoreWeave case study complete</p>
<h3 id="ai-feature-heading"><a href="projects/ai-infrastructure-financing.html">AI Infrastructure and Neocloud Financing</a><span>Borrowing, Leverage and the Assets Behind the AI Build-Out</span></h3>
<p class="feature-question">How much have specialised GPU-cloud companies borrowed, and what assets does that debt finance or secure?</p>
<p>The first case study is CoreWeave. Between December 2023 and September 2026 its debt (borrowings plus finance leases) rose from {{hd_2023|plain}} to {{hd_2026|plain}}, and from {{hd_pct_2023|plain}} to {{hd_pct_2026|plain}} of total assets, while its gross property and equipment grew from {{ppe_2023|plain}} to {{ppe_2026|plain}}. The filings say more clearly what lenders hold as security than what each loan paid for. The clearest link is equipment financing from manufacturers, secured by the same equipment it paid for.</p>
<p class="feature-status">SEC filings only, nine reporting dates · Nebius, Lambda, Crusoe and Nscale next</p>
<p class="feature-links"><a class="button" href="projects/ai-infrastructure-financing.html">Read the CoreWeave case study</a></p>
</div>
</article>
<!-- neocloud-card:end -->'''
ENTRY = '''<!-- neocloud-entry:start (generated by scripts/neocloud/render_page.py) -->
<li><p class="work-kicker">Case study complete · Research assistant work · Started November 2026</p><h3><a href="projects/ai-infrastructure-financing.html">AI Infrastructure and Neocloud Financing</a></h3>
<p>How much have specialised GPU-cloud companies borrowed, how has their leverage changed, and what assets has that borrowing financed or secured? The first case study, CoreWeave, finds debt rising from {{hd_2023|plain}} to {{hd_2026|plain}} in under three years, from {{hd_pct_2023|plain}} to {{hd_pct_2026|plain}} of total assets, and maps what its filings can and cannot show the loans paid for.</p>
<p class="work-meta">CoreWeave case study complete · Nebius, Lambda, Crusoe and Nscale next</p></li>
<!-- neocloud-entry:end -->'''


def patch(path, start, end, first_pattern, block):
    s = path.read_text()
    if start in s:
        s = re.sub(re.escape(start) + r'.*?' + re.escape(end), lambda m: block, s, flags=re.S)
    else:
        s, n = re.subn(first_pattern, lambda m: block, s, count=1, flags=re.S)
        assert n == 1, f'could not find the entry to replace in {path.name}'
    path.write_text(s)


patch(ROOT / 'index.html', '<!-- neocloud-card:start', '<!-- neocloud-card:end -->',
      r'<article class="treasury-feature home-feature--wip" id="ai-infrastructure".*?</article>', fill(CARD, 'index.html card'))
patch(ROOT / 'research.html', '<!-- neocloud-entry:start', '<!-- neocloud-entry:end -->',
      r'<li><p class="work-kicker">In progress · Research assistant work · Started November 2026</p><h3><a href="projects/ai-infrastructure-financing.html">.*?</li>', fill(ENTRY, 'research.html entry'))

# ---- checklist for Nicholas ----
rows = ['# CoreWeave case study: every displayed number and its source', '',
        f'Generated by `scripts/neocloud/render_page.py` from `assets/neocloud-2026-11/coreweave/data.json` '
        f'(research commit `{d["research_commit"][:7]}`). Exact values are unrounded; "Evidence Index" is the row of the research '
        f'workbook\'s Evidence Index whose exact value was matched by `extract_coreweave.py`.', '',
        '| Shown | Key | Where | Exact value | Source CSV and cell | Evidence Index | Filing, page |', '|---|---|---|---|---|---|---|']
for k in sorted(used, key=lambda k: list(F).index(k)):
    f = F[k]
    doc = docs.get(f['doc'], {})
    rows.append(f"| {f['shown']} | `{k}` | {', '.join(sorted(used[k]))} | {f['exact'][:14]} | {f['source']} | {f.get('evidence_ref', '')} | [{doc.get('short', '')}]({doc.get('url', '')}) p. {f['page']} |")
rows += ['', 'Chart values come from the same data file and are listed with their filing and page in each `exhibit-*.csv`.']
CHECKLIST.write_text('\n'.join(rows) + '\n')
print(f'rendered {PAGE.relative_to(ROOT)}: {len(used)} numbers used ({sum(1 for k in used if F[k].get("evidence_ref"))} matched to the Evidence Index), '
      f'{len(F) - len(used)} extracted but not shown')
