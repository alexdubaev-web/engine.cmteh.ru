"""Create an isolated preview build for data/SEO regression scripts."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def build_fixture():
    source = Path(__file__).resolve().parents[1]
    temporary = tempfile.TemporaryDirectory(prefix='engine-build-test-')
    root = Path(temporary.name)
    for item in ['build.py', 'seo.py', 'pipeline_io.py', 'data', 'public', 'docs', 'src', '.openai']:
        shutil.copytree(source / item, root / item) if (source / item).is_dir() else shutil.copy2(source / item, root / item)
    (root / 'backend').mkdir()
    shutil.copy2(source / 'backend/catalog.json', root / 'backend/catalog.json')
    env = {**os.environ, 'INDEXABLE': 'false', 'PUBLIC_SITE_URL': '', 'INDEXNOW_KEY': ''}
    result = subprocess.run([sys.executable, 'build.py'], cwd=root, env=env, capture_output=True, text=True)
    if result.returncode:
        temporary.cleanup()
        raise RuntimeError('Controlled preview build failed: ' + result.stderr)
    return temporary, root
