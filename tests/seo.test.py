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
 source=f.read_text(encoding="utf-8");h=html.fromstring(source);path='/'+str(f.parent.relative_to(out)).strip('.')+'/' if f.parent!=out else '/';path=path.replace('//','/')
 require(' — ' not in source,path+' generated HTML contains a spaced em dash')
 icons=h.xpath('//link[@rel="icon"]');require(len(icons)==3 and all(icon.get('href','').startswith('/assets/favicon') and '?v=' in icon.get('href','') for icon in icons),path+' versioned raster favicon set missing')
 require([icon.get('type') for icon in icons]==['image/webp','image/webp','image/x-icon'],path+' WebP or ICO browser fallback missing')
 desc=h.xpath('string(//meta[@name="description"]/@content)');descriptions.append(desc);h1s.append(h.xpath('string(//h1)'));heads.append(h.xpath('string(//title)'))
 require(bool(desc),path+' description missing');require(len(h.xpath('//meta[@name="description"]'))==1,path+' duplicate meta')
 require(bool(h.xpath('//meta[@property="og:site_name"]')),path+' missing OG site name')
 require(bool(h.xpath('//nav[@aria-label="Основная навигация"]/a[@href="/about/"]')),path+' header About link missing')
 require(bool(h.xpath('//body[@id="top"]//a[@href="#top"][@aria-label="Наверх"]')),path+' back-to-top fallback missing')
 require('@media(max-width:1150px)' in h.xpath('string(//noscript/style)') and '.nav{position:static;order:3;flex:1 0 100%' in h.xpath('string(//noscript/style)'),path+' no-JS navigation must wrap through the tablet width')
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
 require(p['shortName'] in product['name'],p['sku']+' schema name differs from visible card name')
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
home=html.fromstring((out/'index.html').read_text(encoding='utf-8'))
nojs_nav=home.xpath('string(//head/noscript/style)')
require('position:static' in nojs_nav and 'flex-wrap:wrap' in nojs_nav,'no-JS mobile navigation must stay in document flow')
require(home.xpath('string(//title)')=='Топливная аппаратура Bosch, Delphi, Denso, John Deere | СМ ТЕХНО','home title differs from approved title')
require(home.xpath('string(//meta[@name="description"]/@content)')=='Топливная аппаратура Bosch, Delphi, Denso, John Deere и VDO: форсунки, ТНВД, распылители и клапаны. Подбор по артикулу, цены, наличие и доставка по России.','home description differs from approved description')
require(home.xpath('string(//h1)')=='Топливная аппаратура для дизельной спецтехники','home H1 missing topic')
require(len(home.xpath('//section[@id="catalog"]//article[contains(@class,"product-card")]'))==8,'home must contain exactly eight rendered product cards')
for href in ['/catalog/','/#selection','/#how-to-order','/delivery/','/articles/','/about/','/contacts/']:
 require(bool(home.xpath('//nav[@aria-label="Основная навигация"]/a[@href=$href]',href=href)),'header navigation missing '+href)
require(bool(home.xpath('//footer//a[@href="/catalog/"]')),'footer direct catalog link missing')
for href in ['tel:+78124688299','tel:+79119212213','tel:+79119212214','tel:+79658185687','mailto:info@cmteh.ru','mailto:sale@cmteh.ru']:
 require(bool(home.xpath('//section[contains(@class,"company-summary")]//a[@href=$href]',href=href)),'home contact missing '+href)
require(not home.xpath('//section[contains(@class,"company-summary")]//p/p'),'home company contact block has invalid nested paragraph')
require(not home.xpath('//section[contains(@class,"company-summary")]//dl'),'home company summary must not show legal details')
about=html.fromstring((out/'about'/'index.html').read_text(encoding='utf-8'))
require(not about.xpath('//main//dl[contains(@class,"specs")]'),'About page must not show legal details')
require('по конкретному заказу' in about.text_content(),'About page order copy typo or wording regression')
require(bool(home.xpath('//section[contains(@class,"company-summary")]//a[@href="/about/"]')),'home company summary link missing')
contacts=html.fromstring((out/'contacts'/'index.html').read_text(encoding='utf-8'))
require(contacts.xpath('string(//h1)')=='Контакты','contacts H1 must be Контакты')
require(bool(contacts.xpath('//main//h2[normalize-space(.)="Реквизиты компании"]')),'contacts legal details heading missing')
legal_text=contacts.xpath('string(//main//h2[normalize-space(.)="Реквизиты компании"]/following-sibling::dl[1])')
for value in ['ООО «СМ ТЕХНО»','7804702073','780401001','1237800071410','Санкт-Петербург']:
 require(value in legal_text,'contacts legal details missing '+value)
require(bool(about.xpath('//a[@href="/catalog/"]')) and bool(about.xpath('//a[@href="/delivery/"]')) and bool(about.xpath('//a[@href="/contacts/"]')),'About page navigation links missing')
require(bool(contacts.xpath('//a[@href="tel:+78124688299"]')),'published phone missing on contacts')
require(bool(contacts.xpath('//a[@href="mailto:info@cmteh.ru"]')),'published email missing on contacts')
for href in ['tel:+79119212213','tel:+79119212214','tel:+79658185687','mailto:sale@cmteh.ru']:
 require(bool(contacts.xpath('//a[@href=$href]',href=href)),'additional published contact missing '+href)
identity=next(n for n in graph(contacts) if n.get('@type')=='Organization')
require(identity.get('telephone')==['+7 812 468-82-99','+7 911 921-22-13','+7 911 921-22-14','+7 965 818-56-87'],'Organization telephone data differs from verified contacts')
require(identity.get('email')==['info@cmteh.ru','sale@cmteh.ru'],'Organization email data differs from verified contacts')
require(identity.get('legalName')=='ООО «СМ ТЕХНО»','Organization legalName must remain a string')
delivery=html.fromstring((out/'delivery'/'index.html').read_text(encoding='utf-8'))
commerce=json.loads((Path(__file__).parents[1]/'data/commerce.json').read_text(encoding='utf-8'))['company']
require(commerce['payment_terms'] in delivery.text_content(),'configured payment terms missing from delivery')
require(commerce['delivery_terms'] in delivery.text_content(),'configured delivery terms missing from delivery')
require('подтверждаются менеджером до выставления счёта' in delivery.text_content(),'delivery price/availability confirmation missing')
require(bool(delivery.xpath('//a[normalize-space(.)="Отправить запрос"]')) and bool(delivery.xpath('//a[normalize-space(.)="Подобрать запчасть"]')),'delivery CTAs missing')
app=(Path(__file__).parents[1]/'public/assets/app.js').read_text(encoding='utf-8')
require("params.get('q')" in app and "params.get('brand')" in app and "params.get('sort')" in app,'full catalog query parameters are not initialized')
require("location.href='/catalog/'" in app,'home search and filters do not navigate to full catalog')
sitemap=etree.parse(str(out/'sitemap.xml'));ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9','i':'http://www.google.com/schemas/sitemap-image/1.1'}
urls=sitemap.xpath('//s:loc/text()',namespaces=ns)
require(len(urls)==len(set(urls)),'duplicate sitemap URLs')
require(not any(urlsplit(u).path in ['/404/','/privacy/','/consent/'] for u in urls),'utility page in sitemap')
require(len(sitemap.xpath('//s:lastmod',namespaces=ns))==len(urls),'missing truthful lastmod')
require(len(sitemap.xpath('//i:image',namespaces=ns))==58,'image sitemap does not cover all 58 product photos')
require(all(urlsplit(u).path.endswith('/') for u in urls),'noncanonical URL in sitemap')
require((out/'robots.txt').stat().st_size<500_000,'robots oversized')
require((out/'assets/favicon-32.webp').is_file() and (out/'assets/favicon-64.webp').is_file() and (out/'assets/favicon.ico').is_file(),'optimized WebP and ICO favicon assets missing')
assert not errors,'\n'.join(errors)
print(f'PASS SEO: {len(heads)} pages, 58 unique product texts, metadata/H1, breadcrumbs, schema parity, precise prices, utility noindex, 58 image sitemap entries')
