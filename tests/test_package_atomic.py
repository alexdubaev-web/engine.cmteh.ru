import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_ru


class PackageAtomicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ['dist', 'backend/api', 'data', 'docs']:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        (self.root / 'dist/index.html').write_text('fresh page', encoding='utf-8')
        (self.root / 'backend/api/index.php').write_text('api', encoding='utf-8')
        (self.root / 'data/seo-changes.json').write_text('{"indexable":false}', encoding='utf-8')
        (self.root / 'data/products.json').write_text('[]', encoding='utf-8')
        (self.root / 'data/seo-catalog.json').write_text('[]', encoding='utf-8')
        (self.root / 'docs/HOSTING-RU.md').write_text('host', encoding='utf-8')
        (self.root / 'docs/SEO-YANDEX.md').write_text('seo', encoding='utf-8')
        (self.root / 'release-ru/public_html').mkdir(parents=True)
        (self.root / 'release-ru/public_html/marker.txt').write_text('last good release', encoding='utf-8')
        self.archive = self.root / 'last-good.zip'
        self.archive.write_bytes(b'last good archive')
        self.release = self.root / 'release-ru'
        with patch.object(package_ru, 'ROOT', self.root):
            pass

    def tearDown(self):
        self.temp.cleanup()

    def assert_old_outputs(self):
        self.assertEqual((self.release / 'public_html/marker.txt').read_text(encoding='utf-8'), 'last good release')
        self.assertEqual(self.archive.read_bytes(), b'last good archive')

    def run_with_replace_failure(self, fail):
        original = package_ru.os.replace
        def replacement(source, target):
            if fail(Path(source), Path(target)):
                raise OSError('injected replace failure')
            return original(source, target)
        with patch.object(package_ru, 'ROOT', self.root), patch.object(package_ru.os, 'replace', side_effect=replacement):
            with self.assertRaises(OSError):
                package_ru.package(self.archive)
        self.assert_old_outputs()

    def test_first_release_move_failure_preserves_both_outputs(self):
        self.run_with_replace_failure(lambda src, dst: src == self.release)

    def test_archive_backup_copy_failure_preserves_both_outputs(self):
        original = package_ru.shutil.copy2
        def copy(source, target, *args, **kwargs):
            if Path(source) == self.archive:
                raise OSError('injected archive backup failure')
            return original(source, target, *args, **kwargs)
        with patch.object(package_ru, 'ROOT', self.root), patch.object(package_ru.shutil, 'copy2', side_effect=copy):
            with self.assertRaises(OSError):
                package_ru.package(self.archive)
        self.assert_old_outputs()

    def test_final_archive_replace_failure_restores_release_and_keeps_archive(self):
        self.run_with_replace_failure(lambda src, dst: src.name == 'archive.zip')

    def test_zip_creation_failure_preserves_release_and_archive(self):
        with patch.object(package_ru, 'ROOT', self.root), patch.object(package_ru.zipfile, 'ZipFile', side_effect=OSError('injected zip failure')):
            with self.assertRaises(OSError):package_ru.package(self.archive)
        self.assert_old_outputs()

    def test_success_publishes_release_and_complete_archive(self):
        with patch.object(package_ru, 'ROOT', self.root):package_ru.package(self.archive)
        self.assertTrue((self.release / 'public_html/index.html').is_file())
        with package_ru.zipfile.ZipFile(self.archive) as archive:
            self.assertIn('public_html/index.html', archive.namelist())
            self.assertIn('public_html/api/index.php', archive.namelist())


if __name__ == '__main__':
    unittest.main()
