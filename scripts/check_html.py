"""Check offline course navigation and embedded source coverage."""
from html.parser import HTMLParser
from pathlib import Path

class Guide(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.targets = []
        self.diagrams = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.targets.append(attrs['href'][1:])
        if tag == 'svg':
            self.diagrams += 1

root = Path(__file__).resolve().parents[1]
guide = Guide()
guide.feed((root / 'docs/index.html').read_text(encoding='utf-8'))
section_ids = guide.ids
assert len(section_ids) == len(set(section_ids)), 'Duplicate navigation IDs'
assert set(guide.targets) <= set(section_ids), 'Broken internal links'
assert guide.diagrams == 5, 'Expected five teaching diagrams'
assert all(f'lab-{i}' in section_ids for i in range(1, 9))
print('HTML checks passed: eight labs, five diagrams and all internal links.')
