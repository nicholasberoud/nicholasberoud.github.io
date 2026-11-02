"""Package reviewed portfolio content and validate local links before publishing."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
SITE_HOST = 'nicholasberoud.github.io'
PAGES = (
    'index.html',
    'research.html',
    '404.html',
    'projects/fima.html',
    'projects/term-premium.html',
    'projects/term-premium/deficits-and-the-term-premium.html',
    'projects/term-premium/lab-notes-2026-10.html',
    'projects/term-premium/em-sovereign-credit.html',
    'projects/term-premium/where-is-the-fed.html',
    'projects/term-premium/brazil-eight-sigma.html',
    'projects/repo-market.html',
    'notes/climate-resilience.html',
    'notes/who-buys-the-debt.html',
    'notes/tic-research.html',
)

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                raise ValueError(f'Duplicate HTML id: {attrs["id"]}')
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])

asset_names = [line.strip() for line in (ROOT / 'scripts/public-assets.txt').read_text().splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
if len(asset_names) != len(set(asset_names)):
    raise ValueError('Duplicate entry in public asset manifest')
for name in asset_names:
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or path.parts[0] != 'assets':
        raise ValueError(f'Invalid public asset path: {name}')
asset_paths = list((ROOT / 'assets').rglob('*'))
if (ROOT / 'assets').is_symlink() or any(path.is_symlink() for path in asset_paths):
    raise ValueError('Symlinks are not allowed in public assets')
actual_assets = {path.relative_to(ROOT).as_posix() for path in asset_paths if path.is_file()}
if actual_assets != set(asset_names):
    raise ValueError(f'Public assets need review: unlisted={sorted(actual_assets - set(asset_names))}; '
                     f'missing={sorted(set(asset_names) - actual_assets)}')

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir()
for name in PAGES:
    dest = OUT / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, dest)
for name in asset_names:
    dest = OUT / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, dest)
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
        if url.scheme and url.scheme not in ('http', 'https'):
            continue
        if url.netloc and url.netloc != SITE_HOST:
            continue
        if url.scheme and not url.netloc:
            raise ValueError(f'Malformed URL in {filename.name}: {link}')
        if url.netloc or url.path.startswith('/'):
            target = (OUT / unquote(url.path).lstrip('/')).resolve()
        else:
            target = (filename.parent / unquote(url.path)).resolve() if url.path else filename
        if target.is_dir():
            target /= 'index.html'
        if not target.is_relative_to(OUT.resolve()) or not target.is_file():
            raise ValueError(f'Broken local link in {filename.name}: {link}')
        if url.fragment and target in parsed and unquote(url.fragment) not in parsed[target].ids:
            raise ValueError(f'Missing anchor in {filename.name}: {link}')
        count += 1
print(f'Packaged {len(PAGES)} reviewed pages; checked {count} internal links and assets.')
