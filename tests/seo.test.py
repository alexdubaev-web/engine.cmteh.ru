"""SEO contract checks: crawlability and factual parity, not ranking predictions."""
from pathlib import Path
import json,re,sys
from urllib.parse import urlsplit
from lxml import html,etree
from build_fixture import build_fixture
_fixture,root=build_fixture();out=root/'dist'
products=json.loads((root/'data/products.json').read_text(encoding="utf-8"));availability=json.loads((root/'data/commerce.json').read_text(encoding="utf-8"))['availability'];stock=json.loads((root/'data/stock.json').read_text(encoding="utf-8"))['items'];errors=[];descriptions=[];h1s=[];heads=[]
def require(ok,msg):
 if not ok:errors.append(msg)
def graph(h):
 raw=json.loads(h.xpath('//script[@type="application/ld+json"]/text()')[0]);return raw.get('@graph',[raw])
for f in out.rglob('*.html'):
 h=html.fromstring(f.read_text(encoding="utf-8"));path='/'+str(f.parent.relative_to(out)).strip('.')+'/' if f.parent!=out else '/';path=path.replace('//','/')
 desc=h.xpath('string(//meta[@name="description"]/@content)');descriptions.append(desc);h1s.append(h.xpath('string(//h1)'));heads.append(h.xpath('string(//title)'))
 require(bool(desc),path+' description missing');require(len(h.xpath('//meta[@name="description"]'))==1,path+' duplicate meta')
 require(bool(h.xpath('//meta[@property="og:site_name"]')),path+' missing OG site name')
 for image in h.xpath('//img'):require(image.get('alt') is not None,path+' image missing alt')
 nodes=graph(h);types={n.get('@type') for n in nodes}
 require('Organization' in types and 'WebSite' in types,path+' identity graph missing')
 if path!='/':
  require('BreadcrumbList' in types,path+' breadcrumb schema missing')
  require(bool(h.xpath('//nav[@aria-label="Хлебные крошки"]//li[last()]//*[@aria-current="page"]')),path+' accessible breadcrumbs missing')
  crumb=next(n for n in nodes if n.get('@type')=='BreadcrumbList')
  visible=h.xpath('//nav[@aria-label="Хлебные крошки"]//li')
  require(len(visible)==len(crumb['itemListElement']),path+' breadcrumb graph disagrees with UI')
  require(crumb['itemListElement'][0]['name']=='Главная',path+' breadcrumb root missing')
 if path in ['/404/','/privacy/','/consent/']:
  require('noindex' in h.xpath('string(//meta[@name="robots"]/@content)'),path+' utility page indexed')
 for node in nodes:
  require('aggregateRating' not in node and 'review' not in node,path+' fabricated reviews')
for p in products:
 h=html.fromstring((out/'catalog'/p['id']/'index.html').read_text(encoding="utf-8"));nodes=graph(h);product=next(n for n in nodes if n.get('@type')=='Product')
 require(p['sku'] in h.xpath('string(//h1)'),p['sku']+' SKU missing from H1')
 require(product['name']==h.xpath('string(//h1)'),p['sku']+' Product name differs from H1')
 require(product['offers']['price']==p['price'],p['sku']+' price mismatch')
 require(product['offers']['priceCurrency']=='RUB',p['sku']+' currency mismatch')
 require(h.xpath('string(//article[@itemtype="https://schema.org/Product"]/@itemid)')==product['@id'],p['sku']+' Product microdata missing')
 require(float(h.xpath('string(//meta[@itemprop="price"]/@content)'))==p['price'],p['sku']+' microdata price mismatch')
 require(h.xpath('string(//meta[@itemprop="priceCurrency"]/@content)')=='RUB',p['sku']+' microdata currency mismatch')
 expected=availability.get(p['id']);actual=product['offers'].get('availability')
 require(actual==('https://schema.org/'+expected if expected else None),p['sku']+' unsupported stock status')
 if expected and p['id'] in stock:
  require(product['offers']['inventoryLevel']['value']==stock[p['id']]['quantity'],p['sku']+' stock count mismatch')
  require(str(stock[p['id']]['quantity'])+' шт.' in h.xpath('string(//section[@class="product-detail"]//div[@class="stock-badge"])'),p['sku']+' stock absent from visible card')
 paragraphs=h.xpath('//section[@id="description"]//p/text()');require(len(paragraphs)>=2,p['sku']+' editorial copy missing')
 require(all(text.strip() for text in paragraphs),p['sku']+' empty editorial text')
 require(bool(h.xpath('//a[starts-with(@href,"/articles/")]')),p['sku']+' no article links')
 photo=h.xpath('//div[@class="detail-photo"]/img')
 if photo:
  require(photo[0].get('loading')=='eager' and photo[0].get('fetchpriority')=='high',p['sku']+' product LCP lazy')
  require(p['sku'] in photo[0].get('alt',''),p['sku']+' photo alt not specific')
 if p['price']==293.8:require('293,80' in h.xpath('string(//div[@class="detail-price"])'),'fractional price rounded')
require(len(descriptions)==len(set(descriptions)),'duplicate descriptions');require(len(heads)==len(set(heads)),'duplicate titles');require(len(h1s)==len(set(h1s)),'duplicate H1')
sitemap=etree.parse(str(out/'sitemap.xml'));ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9','i':'http://www.google.com/schemas/sitemap-image/1.1'}
urls=sitemap.xpath('//s:loc/text()',namespaces=ns)
require(len(urls)==len(set(urls)),'duplicate sitemap URLs')
require(not any(urlsplit(u).path in ['/404/','/privacy/','/consent/'] for u in urls),'utility page in sitemap')
require(len(sitemap.xpath('//s:lastmod',namespaces=ns))==len(urls),'missing truthful lastmod')
require(len(sitemap.xpath('//i:image',namespaces=ns))==25,'image sitemap does not cover 25 actual product photos')
require(all(urlsplit(u).path.endswith('/') for u in urls),'noncanonical URL in sitemap')
require((out/'robots.txt').stat().st_size<500_000,'robots oversized')
assert not errors,'\n'.join(errors)
print(f'PASS SEO: {len(heads)} pages, 58 unique product texts, metadata/H1, breadcrumbs, schema parity, precise prices, utility noindex, 25 image sitemap entries')
