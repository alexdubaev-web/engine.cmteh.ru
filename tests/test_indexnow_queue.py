import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tools.indexnow as indexnow


class IndexNowQueueTests(unittest.TestCase):
    def test_cli_dry_run_uses_its_repo_root_and_never_submits(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'tools').mkdir();(root/'data').mkdir()
            import shutil
            shutil.copy2(Path(indexnow.__file__),root/'tools/indexnow.py')
            shutil.copy2(Path(indexnow.__file__).parents[1]/'pipeline_io.py',root/'pipeline_io.py')
            (root/'data/seo-changes.json').write_text(json.dumps({'origin':'https://engine.cmteh.ru','indexable':True,
                'urls':['https://engine.cmteh.ru/catalog/a/'],'revisions':{'https://engine.cmteh.ru/catalog/a/':'r1'}}),encoding='utf-8')
            env={**os.environ,'INDEXNOW_KEY':'test-key-12345678'}
            result=subprocess.run([sys.executable,str(root/'tools/indexnow.py'),'submit','--dry-run'],cwd=root,env=env,
                                  capture_output=True,text=True,check=True)
            self.assertIn('"urlCount": 1',result.stdout)
    def test_acknowledgement_keeps_same_url_changed_during_request(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path = root / 'data/seo-changes.json'
            state_path.parent.mkdir()
            state_path.write_text(json.dumps({'urls': ['https://example.com/a'],
                                              'revisions': {'https://example.com/a': 'new'}}), encoding='utf-8')
            with patch.object(indexnow, 'ROOT', root):
                remaining = indexnow.acknowledge({'https://example.com/a': 'old'})
            self.assertEqual(remaining, ['https://example.com/a'])
            self.assertEqual(json.loads(state_path.read_text(encoding='utf-8'))['revisions']['https://example.com/a'], 'new')

    def test_in_flight_snapshot_ack_preserves_new_and_updated_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);state_path = root / 'data/seo-changes.json';state_path.parent.mkdir()
            initial = {'generated_at': 'g1', 'urls': ['https://example.com/a'],
                       'revisions': {'https://example.com/a': 'old-a'}}
            state_path.write_text(json.dumps(initial), encoding='utf-8')
            with patch.object(indexnow, 'ROOT', root):
                snapshot, tokens = indexnow.snapshot_queue()
                latest = {'generated_at': 'g2', 'urls': ['https://example.com/a', 'https://example.com/b'],
                          'revisions': {'https://example.com/a': 'new-a', 'https://example.com/b': 'new-b'}}
                state_path.write_text(json.dumps(latest), encoding='utf-8')
                remaining = indexnow.acknowledge(tokens)
            self.assertEqual(remaining, latest['urls'])
            self.assertEqual(json.loads(state_path.read_text(encoding='utf-8'))['revisions'], latest['revisions'])

    def test_failed_atomic_ack_write_keeps_original_queue_parseable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);state_path = root / 'data/seo-changes.json';state_path.parent.mkdir()
            original = {'urls': ['https://example.com/a'], 'revisions': {'https://example.com/a': 'r1'}}
            state_path.write_text(json.dumps(original), encoding='utf-8')
            with patch.object(indexnow, 'ROOT', root), patch.object(indexnow, 'atomic_write_text', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):indexnow.acknowledge({'https://example.com/a': 'r1'})
            self.assertEqual(json.loads(state_path.read_text(encoding='utf-8')), original)


if __name__ == '__main__':
    unittest.main()
