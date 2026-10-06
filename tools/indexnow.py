#!/usr/bin/env python3
"""Notify Yandex about new/changed URLs only; never handles personal data."""
from pathlib import Path
from urllib.parse import urlsplit
import argparse,json,os,re,secrets,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['key','check','submit']);p.add_argument('--dry-run',action='store_true');args=p.parse_args()
if args.command=='key':print(secrets.token_hex(16));raise SystemExit
state=json.loads((ROOT/'data/seo-changes.json').read_text());origin=state['origin'];key=os.environ.get('INDEXNOW_KEY','')
if not state.get('indexable') or '.chatgpt.site' in urlsplit(origin).hostname:raise SystemExit('Build an indexable production domain first; demo notification is disabled.')
if not re.fullmatch('[a-zA-Z0-9-]{8,128}',key):raise SystemExit('Set INDEXNOW_KEY and rebuild to publish its verification file.')
key_url=origin+'/'+key+'.txt';urls=state['urls']
if any(urlsplit(url).scheme!='https' or urlsplit(url).netloc!=urlsplit(origin).netloc for url in urls):raise SystemExit('Foreign URL rejected')
payload={'host':urlsplit(origin).hostname,'key':key,'keyLocation':key_url,'urlList':urls}
if args.dry_run:
 print(json.dumps({'endpoint':'https://yandex.com/indexnow','keyLocation':key_url,'urlCount':len(urls),'urls':urls},ensure_ascii=False,indent=2));raise SystemExit
try:
 with urllib.request.urlopen(key_url,timeout=20) as response:
  if response.status!=200 or response.read(1024).decode().strip()!=key:raise SystemExit('Deployed verification file does not match')
 if args.command=='check':print('Deployed key verified; pending URLs:',len(urls));raise SystemExit
 if not urls:print('No pending changes to submit');raise SystemExit
 for start in range(0,len(urls),10000):
  batch={**payload,'urlList':urls[start:start+10000]};request=urllib.request.Request('https://yandex.com/indexnow',data=json.dumps(batch).encode(),headers={'Content-Type':'application/json'},method='POST')
  with urllib.request.urlopen(request,timeout=30) as response:
   if response.status not in [200,202]:raise SystemExit('Submission not accepted: '+str(response.status))
   print('IndexNow accepted batch:',len(batch['urlList']),'URLs; HTTP',response.status)
 state['urls']=[];(ROOT/'data/seo-changes.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
except urllib.error.HTTPError as error:raise SystemExit('IndexNow HTTP '+str(error.code)+'; pending changes retained')
except urllib.error.URLError:raise SystemExit('Network error; pending changes retained')
