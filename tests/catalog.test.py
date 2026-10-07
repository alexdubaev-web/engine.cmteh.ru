from pathlib import Path
import hashlib
import json,re,sys
from urllib.parse import urlsplit
import lxml.html
from PIL import Image
from build_fixture import build_fixture
_fixture,root=build_fixture();out=root/'dist';products=json.loads((root/'data/products.json').read_text(encoding="utf-8"));pages=list(out.rglob('*.html'));errors=[];titles=[];availability=json.loads((root/'data/commerce.json').read_text(encoding="utf-8"))['availability']
for p in pages:
 s=p.read_text(encoding="utf-8");h=lxml.html.fromstring(s)
 if re.search('[\u3400-\u9fff]',h.text_content()):errors.append(str(p)+' CJK text')
 if len(h.xpath('//h1'))!=1:errors.append(str(p)+' H1 count')
 title=h.xpath('//title/text()');titles+=title
 if not h.xpath('//meta[@name="description"]/@content'):errors.append(str(p)+' missing description')
 for tag,attr in [('a','href'),('img','src'),('script','src'),('link','href')]:
  for href in h.xpath('//'+tag+'/@'+attr):
   if not href.startswith('/') or href.startswith('//'):continue
   path=urlsplit(href).path;target=out/path.strip('/')
   if path.endswith('/'):target=target/'index.html'
   if not target.exists():errors.append(str(p)+' broken link '+href)
 for raw in h.xpath('//script[@type="application/ld+json"]/text()'):json.loads(raw)
for p in products:
 h=lxml.html.fromstring((out/'catalog'/p['id']/'index.html').read_text(encoding="utf-8"));graph=json.loads(h.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph'];product=graph[0]
 assert 'Внешний вид и комплектность уточняются при заказе.' in h.text_content(),p['id']+' generic image note missing'
 assert not h.xpath('//a[normalize-space(.)="Источник фотографии"]'),p['id']+' source photo claim is visible'
 if product['offers']['price']!=p['price']:errors.append(p['id']+' price mismatch')
 if product['sku']!=p['sku']:errors.append(p['id']+' sku mismatch')
 expected=availability.get(p['id']);actual=product['offers'].get('availability')
 if actual!=('https://schema.org/'+expected if expected else None):errors.append(p['id']+' unjustified availability')
assert len(products)==58
image_manifest=json.loads((root/'data/images.json').read_text(encoding='utf-8'))
image_dimensions=json.loads((root/'data/image-dimensions.json').read_text(encoding='utf-8'))
image_ledger=json.loads((root/'docs/PRODUCT-IMAGES-2026-10-07.json').read_text(encoding='utf-8'))
manifest={row['id']:row for row in image_manifest}
ledger={row['id']:row for row in image_ledger['products']}
assert len(manifest)==58 and set(manifest)=={p['id'] for p in products},'Image manifest must cover all 58 catalog products'
assert len(image_dimensions)==58,'Image dimensions must cover all 58 product assets'
assert set(ledger)==set(manifest),'Image provenance ledger must cover all 58 products'
for product in products:
 row=manifest[product['id']];entry=ledger[product['id']];image=row.get('image')
 assert image==f"/assets/part-{product['id']}-v2.webp",product['id']+' missing versioned WebP image'
 target=root/'public'/image.lstrip('/')
 assert target.is_file(),product['id']+' image asset missing'
 assert target.stat().st_size<=150_000,product['id']+' image exceeds 150 KB'
 with Image.open(target) as decoded:
  decoded.load()
  assert decoded.format=='WEBP',product['id']+' image is not WebP'
  assert list(decoded.size)==image_dimensions[image]==[entry['width'],entry['height']],product['id']+' image dimensions mismatch'
 assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256'],product['id']+' image provenance digest mismatch'
assert not list((root/'public/assets').glob('part-*.webp')) or all(p.name.endswith('-v2.webp') for p in (root/'public/assets').glob('part-*.webp')),'Legacy product image paths remain'
with Image.open(root/'public/assets/logo.webp') as logo:
 logo.load();assert logo.format=='WEBP' and logo.size==(400,148),'Logo must be a 2x WebP asset'
assert len(set(titles))==len(titles),'Duplicate titles'
assert not errors,'\n'.join(errors)
print(f'PASS: {len(pages)} HTML pages, 58 SKU/price matches, internal links, JSON-LD, unique titles, no Chinese text')
