#!/usr/bin/env python3
"""Notify Yandex about new/changed URLs only; never handles personal data."""
from pathlib import Path
from urllib.parse import urlsplit
import argparse
import json
import os
import re
import secrets
import sys
import urllib.request
import urllib.error
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline_io import atomic_write_text, pipeline_lock

ROOT = Path(__file__).resolve().parents[1]


def snapshot_queue():
    with pipeline_lock(ROOT):
        state = json.loads((ROOT / 'data/seo-changes.json').read_text(encoding='utf-8'))
        revisions = state.get('revisions', {})
        tokens = {url: revisions.get(url, state.get('generated_at', 'legacy')) for url in state['urls']}
        return state, tokens


def acknowledge(tokens):
    """Remove only sent URL generations that are still the queued generation."""
    with pipeline_lock(ROOT):
        path = ROOT / 'data/seo-changes.json'
        state = json.loads(path.read_text(encoding='utf-8'))
        revisions = state.setdefault('revisions', {})
        sent = set(tokens)
        kept = []
        for url in state.get('urls', []):
            current = revisions.get(url, state.get('generated_at', 'legacy'))
            if url in sent and current == tokens[url]:
                revisions.pop(url, None)
            else:
                kept.append(url)
        state['urls'] = kept
        atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=2) + '\n')
        return kept


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['key', 'check', 'submit'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.command == 'key':
        print(secrets.token_hex(16))
        return
    state, tokens = snapshot_queue()
    origin = state['origin']
    key = os.environ.get('INDEXNOW_KEY', '')
    if not state.get('indexable') or '.chatgpt.site' in urlsplit(origin).hostname:
        raise SystemExit('Build an indexable production domain first; demo notification is disabled.')
    if not re.fullmatch('[a-zA-Z0-9-]{8,128}', key):
        raise SystemExit('Set INDEXNOW_KEY and rebuild to publish its verification file.')
    key_url = origin + '/' + key + '.txt'
    urls = list(tokens)
    if any(urlsplit(url).scheme != 'https' or urlsplit(url).netloc != urlsplit(origin).netloc for url in urls):
        raise SystemExit('Foreign URL rejected')
    if args.dry_run:
        print(json.dumps({'endpoint': 'https://yandex.com/indexnow', 'keyLocation': key_url,
                          'urlCount': len(urls), 'urls': urls}, ensure_ascii=False, indent=2))
        return
    try:
        with urllib.request.urlopen(key_url, timeout=20) as response:
            if response.status != 200 or response.read(1024).decode('utf-8').strip() != key:
                raise SystemExit('Deployed verification file does not match')
        if args.command == 'check':
            print('Deployed key verified; pending URLs:', len(urls))
            return
        if not urls:
            print('No pending changes to submit')
            return
        for start in range(0, len(urls), 10000):
            batch = {'host': urlsplit(origin).hostname, 'key': key, 'keyLocation': key_url,
                     'urlList': urls[start:start + 10000]}
            request = urllib.request.Request('https://yandex.com/indexnow', data=json.dumps(batch).encode('utf-8'),
                                             headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status not in [200, 202]:
                    raise SystemExit('Submission not accepted: ' + str(response.status))
                print('IndexNow accepted batch:', len(batch['urlList']), 'URLs; HTTP', response.status)
        acknowledge(tokens)
    except urllib.error.HTTPError as error:
        raise SystemExit('IndexNow HTTP ' + str(error.code) + '; pending changes retained')
    except urllib.error.URLError:
        raise SystemExit('Network error; pending changes retained')


if __name__ == '__main__':
    main()
