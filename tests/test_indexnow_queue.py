import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tools.indexnow as indexnow
from seo import SEO


class IndexNowQueueTests(unittest.TestCase):
    def test_cli_dry_run_uses_config_fallback_env_override_and_explicit_empty_disable(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'tools').mkdir();(root/'data').mkdir()
            shutil.copy2(Path(indexnow.__file__),root/'tools/indexnow.py')
            shutil.copy2(Path(indexnow.__file__).parents[1]/'pipeline_io.py',root/'pipeline_io.py')
            (root/'data/seo-changes.json').write_text(json.dumps({'origin':'https://engine.cmteh.ru','indexable':True,
                'urls':['https://engine.cmteh.ru/catalog/a/'],'revisions':{'https://engine.cmteh.ru/catalog/a/':'r1'}}),encoding='utf-8')
            stored_key='stored-key-12345678'
            (root/'data/commerce.json').write_text(json.dumps({'indexnow_key':stored_key}),encoding='utf-8')
            env={key:value for key,value in os.environ.items() if key!='INDEXNOW_KEY'}
            args=[sys.executable,str(root/'tools/indexnow.py'),'submit','--dry-run']
            result=subprocess.run(args,cwd=root,env=env,
                                  capture_output=True,text=True,check=True)
            self.assertIn('"urlCount": 1',result.stdout)
            self.assertIn('/'+stored_key+'.txt',result.stdout)
            override='override-key-12345678'
            result=subprocess.run(args,cwd=root,env={**env,'INDEXNOW_KEY':override},
                                  capture_output=True,text=True,check=True)
            self.assertIn('/'+override+'.txt',result.stdout)
            self.assertNotIn('/'+stored_key+'.txt',result.stdout)
            result=subprocess.run(args,cwd=root,env={**env,'INDEXNOW_KEY':''},
                                  capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Set INDEXNOW_KEY',result.stderr)
            (root/'data/commerce.json').unlink()
            result=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Set INDEXNOW_KEY',result.stderr)

    def test_build_keyfile_uses_fallback_only_for_indexable_output(self):
        key='build-key-12345678'
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=root/'data';assets=root/'public/assets';data.mkdir(parents=True);assets.mkdir(parents=True)
            (data/'commerce.json').write_text(json.dumps({'indexnow_key':key,'availability':{},'company':{},'yml_enabled':False}),encoding='utf-8')
            for name in ['app.js','style.css','analytics.js','favicon-32.webp','favicon-64.webp','favicon.ico']:
                (assets/name).write_bytes(b'fixture')
            production=root/'production';production.mkdir()
            overridden=root/'overridden';overridden.mkdir()
            preview=root/'preview';preview.mkdir()
            with patch.dict(os.environ,{},clear=True):
                SEO(root,production,'https://engine.cmteh.ru',True,[],{}).finish([])
                SEO(root,preview,'https://cm-techno-diesel.alexdubaev.chatgpt.site',False,[],{}).finish([])
            self.assertEqual((production/(key+'.txt')).read_text(encoding='utf-8'),key)
            self.assertFalse((preview/(key+'.txt')).exists())
            override='override-key-12345678'
            with patch.dict(os.environ,{'INDEXNOW_KEY':override},clear=True):
                SEO(root,overridden,'https://engine.cmteh.ru',True,[],{}).finish([])
            self.assertEqual((overridden/(override+'.txt')).read_text(encoding='utf-8'),override)
            self.assertFalse((overridden/(key+'.txt')).exists())
            disabled=root/'disabled';disabled.mkdir()
            with patch.dict(os.environ,{'INDEXNOW_KEY':''},clear=True):
                SEO(root,disabled,'https://engine.cmteh.ru',True,[],{}).finish([])
            self.assertFalse((disabled/(key+'.txt')).exists())
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
