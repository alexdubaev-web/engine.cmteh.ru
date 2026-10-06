import tempfile
import unittest
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline_io import pipeline_lock, publish_files


class PublishFilesTests(unittest.TestCase):
    def test_failed_second_replace_restores_all_old_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / 'first.json', root / 'second.json'
            new_first, new_second = root / 'stage-first.json', root / 'stage-second.json'
            first.write_text('old first', encoding='utf-8')
            second.write_text('old second', encoding='utf-8')
            new_first.write_text('new first', encoding='utf-8')
            new_second.write_text('new second', encoding='utf-8')

            def fail_second(source, target):
                if Path(target) == second:
                    raise OSError('injected publish failure')
                Path(source).replace(target)

            with self.assertRaises(OSError):
                publish_files({new_first: first, new_second: second}, replace=fail_second)
            self.assertEqual(first.read_text(encoding='utf-8'), 'old first')
            self.assertEqual(second.read_text(encoding='utf-8'), 'old second')

    def test_next_lock_holder_recovers_interrupted_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);target = root / 'data/catalog.json';target.parent.mkdir()
            target.write_text('new', encoding='utf-8')
            backup_root = root / '.pipeline-backup-interrupted';backup_root.mkdir()
            backup = backup_root / '0';backup.write_text('old', encoding='utf-8')
            (root / '.pipeline-publish.json').write_text(json.dumps({'backup_root': str(backup_root), 'entries': [
                {'target': str(target), 'backup': str(backup), 'existed': True}]}), encoding='utf-8')
            with pipeline_lock(root):
                self.assertEqual(target.read_text(encoding='utf-8'), 'old')
            self.assertFalse((root / '.pipeline-publish.json').exists())

    def test_recovery_rejects_target_outside_pipeline_root(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp);target = Path(outside) / 'important.txt';target.write_text('keep', encoding='utf-8')
            backup_root = root / '.pipeline-backup-bad';backup_root.mkdir()
            (root / '.pipeline-publish.json').write_text(json.dumps({'backup_root': str(backup_root), 'entries': [
                {'target': str(target), 'backup': str(backup_root / '0'), 'existed': False}]}), encoding='utf-8')
            with self.assertRaises(ValueError):
                with pipeline_lock(root):pass
            self.assertEqual(target.read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
