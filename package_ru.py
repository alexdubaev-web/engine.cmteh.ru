"""Build a static + PHP package without replacing the last successful release on failure."""
from pathlib import Path
import argparse
import json
import os
import shutil
import tempfile
import zipfile

from apache_config import config as apache_config
from pipeline_io import pipeline_lock

ROOT = Path(__file__).resolve().parent


def package(archive_path):
    dist = ROOT / 'dist'
    if not dist.is_dir() or not any(dist.iterdir()):
        raise FileNotFoundError('Build dist/ successfully before packaging')
    archive = Path(archive_path).expanduser().resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='.package-', dir=ROOT))
    staged = work / 'release-ru'
    web = staged / 'public_html'
    web.mkdir(parents=True)
    release = ROOT / 'release-ru'
    old_release = work / 'old-release'
    old_archive = work / 'old-archive.zip'
    staged_zip = work / 'archive.zip'
    completed = True
    try:
        for item in dist.iterdir():
            if item.name in ['server', '.openai']:
                continue
            destination = web / item.name
            shutil.copytree(item, destination) if item.is_dir() else shutil.copy2(item, destination)
        shutil.copytree(ROOT / 'backend', staged / 'backend', ignore=shutil.ignore_patterns('api', 'config.php', '*.sqlite*'))
        shutil.copytree(ROOT / 'backend/api', web / 'api')
        state = json.loads((ROOT / 'data/seo-changes.json').read_text(encoding='utf-8'))
        products = json.loads((ROOT / 'data/products.json').read_text(encoding='utf-8'))
        (web / '.htaccess').write_text(apache_config(state['indexable'], products), encoding='utf-8')
        shutil.copy2(ROOT / 'docs/HOSTING-RU.md', staged / 'ИНСТРУКЦИЯ.md')
        shutil.copy2(ROOT / 'docs/SEO-YANDEX.md', staged / 'SEO-ЯНДЕКС.md')
        shutil.copy2(ROOT / 'data/seo-catalog.json', staged / 'SEO-КАРТОЧКИ.json')
        for item in web.rglob('*'):
            item.chmod(0o755 if item.is_dir() else 0o644)
        web.chmod(0o755)
        for item in (staged / 'backend').rglob('*'):
            item.chmod(0o750 if item.is_dir() else 0o640)
        (staged / 'backend').chmod(0o750)
        with zipfile.ZipFile(staged_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in sorted(staged.rglob('*')):
                if item.is_file():
                    zf.write(item, item.relative_to(staged))
        old_release_existed = release.exists()
        release_installed = False
        archive_published = False
        archive_backup_ready = False
        completed = False
        try:
            if old_release_existed:
                os.replace(release, old_release)
            os.replace(staged, release)
            release_installed = True
            if archive.exists():
                shutil.copy2(archive, old_archive)
                archive_backup_ready = True
            os.replace(staged_zip, archive)
            archive_published = True
            completed = True
        except BaseException:
            rollback_ok = True
            try:
                if archive_published:
                    if archive_backup_ready and old_archive.exists():
                        os.replace(old_archive, archive)
                    elif archive.exists():
                        archive.unlink()
                if release_installed and release.exists():
                    shutil.rmtree(release)
                if old_release_existed and old_release.exists():
                    os.replace(old_release, release)
            except OSError:
                rollback_ok = False
            if not rollback_ok:
                completed = False
            else:
                completed = True
            raise
        count = sum(item.is_file() for item in release.rglob('*'))
        print(json.dumps({'archive': str(archive), 'files': count, 'sizeKB': round(archive.stat().st_size / 1024)}))
    finally:
        if completed:
            shutil.rmtree(work, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', default=str(ROOT / 'cm-techno-russia.zip'))
    args = parser.parse_args()
    with pipeline_lock(ROOT):
        package(args.archive)


if __name__ == '__main__':
    main()
