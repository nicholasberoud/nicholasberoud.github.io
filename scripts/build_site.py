"""Package reviewed portfolio content and validate local links before publishing."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
PAGES = (
    'index.html',
    '404.html',
    'projects/fima.html',
    'projects/term-premium.html',
    'projects/term-premium/deficits-and-the-term-premium.html',
    'projects/term-premium/lab-notes-2026-10.html',
    'projects/term-premium/em-sovereign-credit.html',
    'projects/term-premium/where-is-the-fed.html',
    'projects/repo-market.html',
    'notes/climate-resilience.html',
    'notes/who-buys-the-debt.html',
)

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
for name in PAGES:
    dest = OUT / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, dest)
shutil.copytree(ROOT / 'assets', OUT / 'assets')
shutil.copy2(ROOT / '.nojekyll', OUT / '.nojekyll')
parsed = {}
for name in PAGES:
    p = Page()
    source = (OUT / name).read_text()
    if 'noindex' in source:
        raise ValueError(f'Unpublished page in deployment: {name}')
    p.feed(source)
    parsed[(OUT / name).resolve()] = p
count = 0
for filename, page in parsed.items():
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (filename.parent / unquote(url.path)).resolve() if url.path else filename
        if target.is_dir():
            target /= 'index.html'
        if not target.is_relative_to(OUT.resolve()) or not target.is_file():
            raise ValueError(f'Broken local link in {filename.name}: {link}')
        if url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
            raise ValueError(f'Missing anchor in {filename.name}: {link}')
        count += 1
print(f'Packaged {len(PAGES)} reviewed pages; checked {count} internal links and assets.')
