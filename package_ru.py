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


def _remove_path(path):
    path = Path(path)
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _remove_archive(path):
    path = Path(path)
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        raise ValueError('Archive recovery target is not a regular file')


def _recover_package_transaction(root, work):
    if (work.parent != root or work.is_symlink() or work.resolve().parent != root
            or not work.name.startswith('.package-')):
        raise ValueError('Invalid package recovery directory')
    marker = work / 'publish.json'
    if not marker.is_file():
        shutil.rmtree(work, ignore_errors=True)
        return
    record = json.loads(marker.read_text(encoding='utf-8'))
    release = Path(record['release'])
    archive = Path(record['archive'])
    old_release = work / 'old-release'
    old_archive = work / 'old-archive.zip'
    if archive.is_symlink():
        raise ValueError('Archive recovery target is a symbolic link')
    resolved_release = (root / 'release-ru').resolve()
    resolved_archive = archive.resolve()
    resolved_work = work.resolve()
    if (release != root / 'release-ru' or not archive.is_absolute()
            or archive != resolved_archive or resolved_archive == resolved_release or resolved_release in resolved_archive.parents
            or resolved_work == resolved_archive or resolved_work in resolved_archive.parents
            or archive.is_symlink() or (archive.exists() and not archive.is_file())):
        raise ValueError('Invalid package recovery journal')
    if record['archive_existed'] and not old_archive.is_file():
        raise ValueError('Package recovery archive backup is missing')

    if record['release_existed']:
        if (old_release.is_symlink() or (old_release.exists() and not old_release.is_dir())
                or old_release.resolve().parent != work.resolve()):
            raise ValueError('Package recovery release backup is invalid')
        if old_release.exists():
            if release.is_symlink() or (release.exists() and release.resolve().parent != root):
                raise ValueError('Package recovery release target escapes its root')
            _remove_path(release)
            shutil.copytree(old_release, release, symlinks=True)
        # If the backup is absent, the first rename did not happen and the
        # existing release is still the last successful one.
    else:
        if release.is_symlink() or (release.exists() and release.resolve().parent != root):
            raise ValueError('Package recovery release target escapes its root')
        _remove_path(release)

    if record['archive_existed']:
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_archive, archive)
    else:
        _remove_archive(archive)
    marker.unlink()
    shutil.rmtree(work, ignore_errors=True)


def recover_package_transactions(root):
    root = Path(root).resolve()
    for work in root.glob('.package-*'):
        if work.is_dir():
            _recover_package_transaction(root, work)


def package(archive_path):
    recover_package_transactions(ROOT)
    dist = ROOT / 'dist'
    if not dist.is_dir() or not any(dist.iterdir()):
        raise FileNotFoundError('Build dist/ successfully before packaging')
    release = ROOT / 'release-ru'
    if (release.is_symlink() or (release.exists() and not release.is_dir())
            or (release.exists() and release.resolve().parent != ROOT.resolve())):
        raise ValueError('release-ru must be a regular directory')
    archive_input = Path(archive_path).expanduser()
    if archive_input.is_symlink():
        raise ValueError('Archive path must not be a symbolic link')
    archive = archive_input.resolve()
    if archive == (ROOT / 'release-ru').resolve() or (ROOT / 'release-ru').resolve() in archive.parents:
        raise ValueError('Archive must be outside release-ru')
    if archive.is_symlink() or (archive.exists() and not archive.is_file()):
        raise ValueError('Archive path must be a regular file')
    archive.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='.package-', dir=ROOT))
    staged = work / 'release-ru'
    web = staged / 'public_html'
    web.mkdir(parents=True)
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
        archive_existed = archive.exists()
        if archive_existed:
            shutil.copy2(archive, old_archive)
        completed = False
        marker = work / 'publish.json'
        marker_tmp = work / 'publish.json.tmp'
        marker_tmp.write_text(json.dumps({'release': str(release), 'archive': str(archive),
                                          'release_existed': old_release_existed,
                                          'archive_existed': archive_existed}), encoding='utf-8')
        os.replace(marker_tmp, marker)
        try:
            if old_release_existed:
                os.replace(release, old_release)
            os.replace(staged, release)
            os.replace(staged_zip, archive)
        except BaseException:
            rollback_ok = True
            try:
                _recover_package_transaction(ROOT, work)
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                rollback_ok = False
            if not rollback_ok:
                completed = False
            else:
                completed = True
            raise
        count = sum(item.is_file() for item in release.rglob('*'))
        marker.unlink()
        completed = True
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
