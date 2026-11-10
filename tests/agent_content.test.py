"""Boundary and generated-site checks for Markdown agent representations."""
import json
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from seo import html_to_markdown
from build_fixture import build_fixture

_fixture, ROOT = build_fixture()
OUT = ROOT / 'dist'


class MarkdownBoundaryTests(unittest.TestCase):
    def test_links_escape_labels_and_keep_query_and_fragment(self):
        result = html_to_markdown('<main><p><a href="/catalog/x/?q=a b&amp;brand=X#facts">part ] one</a></p></main>', 'https://example.test/catalog/x/')
        self.assertIn('[part \\] one](https://example.test/catalog/x/?q=a%20b&brand=X#facts)', result)

    def test_table_pipes_and_nested_list_structure_survive(self):
        result = html_to_markdown('<main><table><thead><tr><th>Part</th><th>Notes</th></tr></thead><tbody><tr><td>A|B</td><td>outer <b>bold</b></td></tr></tbody></table><ul><li>Outer<ul><li>Inner</li></ul></li></ul><ol start="3"><li>First</li><li>Second</li></ol></main>', 'https://example.test/')
        self.assertIn('| A\\|B | outer **bold** |', result)
        self.assertIn('- Outer\n  - Inner', result)
        self.assertIn('3. First\n4. Second', result)

    def test_interactive_and_non_main_content_is_excluded(self):
        result = html_to_markdown('<nav>Navigation</nav><main><h1>Facts</h1><form>Form values</form><script>secrets()</script><button>Buy</button><section data-analytics-panel>Cookie</section><footer>Footer</footer><p>Visible</p></main>', 'https://example.test/')
        self.assertIn('# Facts', result)
        self.assertIn('Visible', result)
        for forbidden in ['Navigation', 'Form values', 'secrets()', 'Buy', 'Cookie', 'Footer']:
            self.assertNotIn(forbidden, result)

    def test_standalone_links_controls_list_spacing_and_hidden_void_elements(self):
        result = html_to_markdown('<main><div><a href="/catalog/item/">Product page</a></div><label>Brand<select><option>All brands</option></select></label><ul><li>Read <a href="/source/">source</a> now.</li></ul><p>First<img hidden src="x">After</p><p>Last</p></main>', 'https://example.test/')
        self.assertIn('[Product page](https://example.test/catalog/item/)', result)
        self.assertIn('- Read [source](https://example.test/source/) now.', result)
        self.assertIn('FirstAfter', result)
        self.assertIn('Last', result)
        self.assertNotIn('Brand', result)
        self.assertNotIn('All brands', result)
        self.assertNotIn('FirstAfterLast', result)


class GeneratedMarkdownTests(unittest.TestCase):
    def test_every_public_html_has_markdown_and_discovery_links(self):
        pages = list(OUT.rglob('*.html'))
        html_paths = set()
        for page in pages:
            rel = page.relative_to(OUT)
            path = '/' if rel == Path('index.html') else '/' + rel.parent.as_posix().strip('./') + '/'
            html_paths.add(path)
            source = page.read_text(encoding='utf-8')
            markdown = page.parent / 'index.md'
            if path == '/404/':
                self.assertFalse(markdown.exists())
                continue
            self.assertTrue(markdown.is_file(), path)
            self.assertIn('rel="alternate" type="text/markdown"', source, path)
            self.assertIn('rel="describedby" href="/llms.txt"', source, path)
            self.assertIn('[Открыть страницу в HTML](', markdown.read_text(encoding='utf-8'), path)
        llms = (OUT / 'llms.txt').read_text(encoding='utf-8')
        self.assertTrue(llms.startswith('# СМ ТЕХНО\n'))
        targets = re.findall(r'\]\((https://[^)]+\.md)\)', llms)
        self.assertTrue(targets)
        for target in targets:
            path = urlsplit(target).path
            self.assertTrue((OUT / path.lstrip('/')).is_file(), target)

    def test_all_product_skus_and_prices_remain_available(self):
        products = json.loads((ROOT / 'data/catalog-built.json').read_text(encoding='utf-8'))
        catalog = (OUT / 'catalog' / 'index.md').read_text(encoding='utf-8')
        links = set(re.findall(r'\]\(https://[^/)]+(/catalog/[^)]+/)\)', catalog))
        self.assertEqual(links, {'/catalog/' + product['id'] + '/' for product in products})
        for product in products:
            markdown = (OUT / 'catalog' / product['id'] / 'index.md').read_text(encoding='utf-8')
            self.assertIn(product['sku'], markdown)
            whole = f"{int(float(product['price'])):,}".replace(',', ' ')
            self.assertTrue(whole in markdown or str(product['price']).replace('.', ',') in markdown, product['id'])


if __name__ == '__main__':
    unittest.main()
