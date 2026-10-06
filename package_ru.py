"""Build a static + PHP package. No credentials, Node or Worker in public_html."""
from pathlib import Path
import shutil,json,zipfile,argparse
from apache_config import config as apache_config
ROOT=Path(__file__).resolve().parent
out=ROOT/'release-ru'
if out.exists():shutil.rmtree(out)
web=out/'public_html';web.mkdir(parents=True)
for f in (ROOT/'dist').iterdir():
 if f.name in ['server','.openai']:continue
 if f.is_dir():shutil.copytree(f,web/f.name)
 else:shutil.copy2(f,web/f.name)
shutil.copytree(ROOT/'backend',out/'backend',ignore=shutil.ignore_patterns('api','config.php','*.sqlite*'))
shutil.copytree(ROOT/'backend/api',web/'api')
state=json.loads((ROOT/'data/seo-changes.json').read_text())
products=json.loads((ROOT/'data/products.json').read_text())
(web/'.htaccess').write_text(apache_config(state['indexable'],products))
shutil.copy2(ROOT/'docs/HOSTING-RU.md',out/'ИНСТРУКЦИЯ.md')
shutil.copy2(ROOT/'docs/SEO-YANDEX.md',out/'SEO-ЯНДЕКС.md')
shutil.copy2(ROOT/'data/seo-catalog.json',out/'SEO-КАРТОЧКИ.json')
# Public files must be readable by the web server after unpacking.
for item in web.rglob('*'):item.chmod(0o755 if item.is_dir() else 0o644)
web.chmod(0o755)
for item in (out/'backend').rglob('*'):item.chmod(0o750 if item.is_dir() else 0o640)
(out/'backend').chmod(0o750)
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',default=str(ROOT/'cm-techno-russia.zip'));args=parser.parse_args()
archive=Path(args.archive).expanduser().resolve()
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(out))
print(json.dumps({'archive':str(archive),'files':sum(f.is_file() for f in out.rglob('*')),'sizeKB':round(archive.stat().st_size/1024)}))
