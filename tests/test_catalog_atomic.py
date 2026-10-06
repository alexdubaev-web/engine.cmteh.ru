import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import import_catalog


class CatalogAtomicTests(unittest.TestCase):
    def test_failed_products_publish_preserves_previous_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            target = root / 'data/products.json'
            previous = '[{"id":"last-good"}]\n'
            target.write_text(previous, encoding='utf-8')
            products = [{'id': 'new-catalog'}]

            original_write_text = Path.write_text
            def fail_direct_target_write(path, data, *args, **kwargs):
                if path == target:
                    original_write_text(path, '[partial', *args, **kwargs)
                    raise OSError('injected interrupted catalog write')
                return original_write_text(path, data, *args, **kwargs)

            original_replace = os.replace
            def fail_atomic_publish(source, destination):
                if Path(destination) == target:
                    raise OSError('injected atomic catalog publish failure')
                return original_replace(source, destination)

            with patch.object(import_catalog, 'ROOT', root), \
                 patch.object(import_catalog, 'parse_catalog', return_value=products), \
                 patch.object(sys, 'argv', ['import_catalog.py', 'catalog.xlsx']), \
                 patch.object(Path, 'write_text', fail_direct_target_write), \
                 patch.object(os, 'replace', side_effect=fail_atomic_publish):
                with self.assertRaises(OSError):
                    import_catalog.main()

            self.assertEqual(target.read_text(encoding='utf-8'), previous)


if __name__ == '__main__':
    unittest.main()
