from pathlib import Path
import json,re,sys
from urllib.parse import urlsplit
import lxml.html
root=Path(__file__).resolve().parents[1];out=root/'dist';products=json.loads((root/'data/products.json').read_text());pages=list(out.rglob('*.html'));errors=[];titles=[];availability=json.loads((root/'data/commerce.json').read_text())['availability']
for p in pages:
 s=p.read_text();h=lxml.html.fromstring(s)
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
 h=lxml.html.fromstring((out/'catalog'/p['id']/'index.html').read_text());graph=json.loads(h.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph'];product=graph[0]
 if product['offers']['price']!=p['price']:errors.append(p['id']+' price mismatch')
 if product['sku']!=p['sku']:errors.append(p['id']+' sku mismatch')
 expected=availability.get(p['id']);actual=product['offers'].get('availability')
 if actual!=('https://schema.org/'+expected if expected else None):errors.append(p['id']+' unjustified availability')
assert len(products)==58
assert len(set(titles))==len(titles),'Duplicate titles'
assert not errors,'\n'.join(errors)
print(f'PASS: {len(pages)} HTML pages, 58 SKU/price matches, internal links, JSON-LD, unique titles, no Chinese text')
