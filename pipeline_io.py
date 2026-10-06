"""Shared cross-process coordination and recoverable multi-file publication."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import threading

_thread_locks = {}
_thread_locks_guard = threading.Lock()


@contextmanager
def pipeline_lock(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    key = str(root.resolve())
    with _thread_locks_guard:
        local_lock = _thread_locks.setdefault(key, threading.Lock())
    local_lock.acquire()
    lock_path = root / '.pipeline.lock'
    try:
        with lock_path.open('a+b') as handle:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                if not handle.read(1):
                    handle.seek(0)
                    handle.write(b'0')
                    handle.flush()
                handle.seek(0)
                while True:
                    try:
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        time.sleep(0.01)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                recover_publish(root)
                yield
            finally:
                if os.name == 'nt':
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        local_lock.release()


def _journal_path(root):
    return Path(root) / '.pipeline-publish.json'


def atomic_write_text(path, value, encoding='utf-8'):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.pipeline-write-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding=encoding, newline='') as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def recover_publish(root):
    """Roll back an interrupted publish before any cooperating reader proceeds."""
    root = Path(root)
    journal = _journal_path(root)
    if not journal.exists():
        return
    record = json.loads(journal.read_text(encoding='utf-8'))
    root_resolved = root.resolve()
    backup_root = Path(record['backup_root']).resolve()
    if backup_root.parent != root_resolved or not backup_root.name.startswith('.pipeline-backup-'):
        raise ValueError('Publish journal backup escapes pipeline root')
    seen = set()
    git_root = root_resolved / '.git'
    for entry in record['entries']:
        target, backup = Path(entry['target']).resolve(), Path(entry['backup']).resolve()
        if (target == root_resolved or not target.is_relative_to(root_resolved)
                or target == backup_root or backup_root in target.parents
                or target == git_root or git_root in target.parents
                or target.parent == root_resolved and target.name in {'.pipeline.lock', '.pipeline-publish.json'}
                or not backup.is_relative_to(backup_root) or backup == backup_root
                or target in seen):
            raise ValueError('Publish journal path escapes its pipeline root')
        seen.add(target)
    for entry in reversed(record['entries']):
        target, backup = Path(entry['target']), Path(entry['backup'])
        if entry['existed']:
            target.parent.mkdir(parents=True, exist_ok=True)
            if backup.is_dir():
                if target.exists():
                    shutil.rmtree(target) if target.is_dir() else target.unlink()
                shutil.copytree(backup, target)
            elif backup.exists():
                shutil.copy2(backup, target)
        elif target.exists():
            shutil.rmtree(target) if target.is_dir() else target.unlink()
    journal.unlink(missing_ok=True)
    shutil.rmtree(backup_root, ignore_errors=True)


def publish_files(files, replace=os.replace, journal_root=None):
    """Publish staged files together, restoring the old set on errors or restart."""
    pairs = [(Path(source), Path(target)) for source, target in files.items()]
    root = Path(journal_root) if journal_root else pairs[0][1].parent
    root.mkdir(parents=True, exist_ok=True)
    root_resolved = root.resolve()
    git_root = root_resolved / '.git'
    seen = set()
    for source, target in pairs:
        resolved = target.resolve()
        if (resolved == root_resolved or not resolved.is_relative_to(root_resolved)
                or resolved == git_root or git_root in resolved.parents
                or resolved.parent == root_resolved and resolved.name in {'.pipeline.lock', '.pipeline-publish.json'}
                or resolved in seen):
            raise ValueError('Publish target must stay within pipeline root')
        seen.add(resolved)
    backup_root = Path(tempfile.mkdtemp(prefix='.pipeline-backup-', dir=root))
    entries = []
    for index, (source, target) in enumerate(pairs):
        backup = backup_root / str(index)
        existed = target.exists()
        if existed:
            if target.is_dir():
                shutil.copytree(target, backup)
            else:
                shutil.copy2(target, backup)
        entries.append({'target': str(target.resolve()), 'backup': str(backup.resolve()), 'existed': existed})
    journal = _journal_path(root)
    journal_tmp = backup_root / 'journal.json'
    journal_tmp.write_text(json.dumps({'backup_root': str(backup_root.resolve()), 'entries': entries}), encoding='utf-8')
    os.replace(journal_tmp, journal)
    try:
        for source, target in pairs:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_dir():
                shutil.rmtree(target)
            replace(source, target)
    except BaseException:
        recover_publish(root)
        raise
    journal.unlink(missing_ok=True)
    shutil.rmtree(backup_root, ignore_errors=True)
