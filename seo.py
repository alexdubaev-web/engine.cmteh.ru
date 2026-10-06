"""Static SEO rendering: factual structured data, stable modification dates, feeds."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import hashlib,html,json,os,re
from xml.etree import ElementTree as ET

CRUMBS={}
UTILITIES={'/404/','/privacy/','/consent/'}
AVAILABILITY={'InStock':'В наличии','OutOfStock':'Нет в наличии','PreOrder':'Предзаказ','BackOrder':'Заказ с ожиданием поставки','LimitedAvailability':'Ограниченное наличие','Discontinued':'Поставка прекращена'}
def esc(value): return html.escape(str(value),quote=True)
def dump(value): return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
def money(value):
 n=Decimal(str(value));s=f'{n:,.2f}' if n%1 else f'{n:,.0f}'
 return s.replace(',',' ').replace('.',',')
def breadcrumbs(items):
 entries=[('Главная','/')]+items
 li=[]
 for i,(name,url) in enumerate(entries):
  item=f'<a href="{esc(url)}">{esc(name)}</a>' if url else f'<span aria-current="page">{esc(name)}</span>'
  li.append('<li>'+('<span aria-hidden="true">/</span>' if i else '')+item+'</li>')
 result='<nav class="wrap breadcrumbs" aria-label="Хлебные крошки"><ol>'+''.join(li)+'</ol></nav>'
 CRUMBS[result]=entries
 return result

class SEO:
 def __init__(self,root,out,base,indexable,products,categories):
  self.root,self.out,self.base,self.indexable,self.products,self.categories=root,out,base,indexable,products,categories
  self.byid={p['id']:p for p in products}
  self.commerce=json.loads((root/'data/commerce.json').read_text())
  self.previous=json.loads((root/'data/seo-state.json').read_text()) if (root/'data/seo-state.json').exists() else {}
  self.current={};self.changed=[];self.now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
  self.asset_versions={n:hashlib.sha256((root/'public/assets'/n).read_bytes()).hexdigest()[:12] for n in ['app.js','style.css']}
 def availability(self,p):
  value=self.commerce['availability'].get(p['id'])
  if value is not None and value not in AVAILABILITY:raise ValueError('Invalid availability for '+p['id'])
  return value
 def product_name(self,p):return p['shortName']+' '+p['brand']+' '+p['sku']
 def product_schema(self,p):
  path='/catalog/'+p['id']+'/'
  offer={'@type':'Offer','@id':self.base+path+'#offer','price':p['price'],'priceCurrency':'RUB','url':self.base+path,'seller':{'@id':self.base+'/#organization'}}
  state=self.availability(p)
  if state:offer['availability']='https://schema.org/'+state
  if state and p.get('stockQuantity') is not None:offer['inventoryLevel']={'@type':'QuantitativeValue','value':p['stockQuantity'],'unitCode':'H87','unitText':'шт.'}
  return {'@context':'https://schema.org','@type':'Product','@id':self.base+path+'#product','name':self.product_name(p),'sku':p['sku'],'brand':{'@type':'Brand','name':p['brand']},'category':self.categories[p['category']][0],'description':p['copy'][0]+' '+p['copy'][1],'url':self.base+path,**({'image':self.base+p['image']} if p.get('image') else {}),'additionalProperty':[{'@type':'PropertyValue','name':'Номер для проверки','value':code} for code in p['codes'] if code!=p['sku']],'offers':offer}
 def identity(self):
  company=self.commerce['company']
  organization={'@type':'Organization','@id':self.base+'/#organization','name':'СМ ТЕХНО','url':self.base+'/','logo':{'@type':'ImageObject','url':self.base+'/assets/logo.jpg'},'areaServed':{'@type':'Country','name':'Россия'}}
  for key,prop in [('legal_name','legalName'),('phone','telephone'),('email','email')]:
   if company.get(key):organization[prop]=company[key]
  if company.get('postal_address'):organization['address']={'@type':'PostalAddress','streetAddress':company['postal_address'],'addressCountry':'RU'}
  website={'@type':'WebSite','@id':self.base+'/#website','url':self.base+'/','name':'СМ ТЕХНО — запчасти для спецтехники','inLanguage':'ru-RU','publisher':{'@id':self.base+'/#organization'}}
  return organization,website
 def render(self,path,title,description,content,schema,header,footer,cart):
  canonical=self.base+path;primary_image='/assets/hero.webp';image_alt='Иллюстрация компонентов дизельной топливной системы'
  product=self.byid.get(path.split('/')[2]) if path.startswith('/catalog/') and path.count('/')==3 else None
  if product:
   primary_image=product.get('image') or '/assets/logo.jpg';image_alt=self.product_name(product) if product.get('image') else 'СМ ТЕХНО'
  organization,website=self.identity();nodes=[]
  if schema:
   incoming=schema.get('@graph',[schema]);nodes=[{k:v for k,v in n.items() if k!='@context'} for n in incoming if n.get('@type') not in ['Organization','WebSite','BreadcrumbList','WebPage']]
  page_type='CollectionPage' if path in ['/catalog/','/articles/'] or path.startswith(('/category/','/brands/')) else 'AboutPage' if path=='/about/' else 'ContactPage' if path=='/contacts/' else 'WebPage'
  web={'@type':page_type,'@id':canonical+'#webpage','url':canonical,'name':title,'description':description,'inLanguage':'ru-RU','isPartOf':{'@id':self.base+'/#website'},'publisher':{'@id':self.base+'/#organization'}}
  trail=next((entries for fragment,entries in CRUMBS.items() if fragment in content),None)
  if trail:
   breadcrumb={'@type':'BreadcrumbList','@id':canonical+'#breadcrumbs','itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':self.base+(url or path)} for i,(name,url) in enumerate(trail)]}
   web['breadcrumb']={'@id':breadcrumb['@id']};nodes.append(breadcrumb)
  items=self.products if path=='/catalog/' else [p for p in self.products if p['category']==path.split('/')[2]] if path.startswith('/category/') else [p for p in self.products if p['brand']==next((v for k,v in {'bosch':'Bosch','delphi':'Delphi','denso':'Denso','john-deere':'John Deere','vdo':'VDO / Vitesco (Aumovio)'}.items() if k==path.split('/')[2]),'')] if path.startswith('/brands/') else []
  if items:
   nodes.append({'@type':'ItemList','@id':canonical+'#list','name':title,'numberOfItems':len(items),'itemListElement':[{'@type':'ListItem','position':i+1,'name':self.product_name(p),'url':self.base+'/catalog/'+p['id']+'/'} for i,p in enumerate(items)]})
  if product:web['mainEntity']={'@id':canonical+'#product'}
  for node in nodes:
   if node.get('@type')=='Article':
    node['@id']=canonical+'#article';node['author']={'@id':self.base+'/#organization'};node['publisher']={'@id':self.base+'/#organization'};node['mainEntityOfPage']={'@id':canonical+'#webpage'};web['mainEntity']={'@id':node['@id']}
  # Hash meaningful content, not the build clock or CSS version.
  digest=hashlib.sha256(dump([path,title,description,content,nodes,organization]).encode()).hexdigest();old=self.previous.get(path,{})
  modified=old.get('lastmod') if old.get('sha256')==digest else self.now
  self.current[path]={'sha256':digest,'lastmod':modified}
  if old.get('sha256')!=digest and path not in UTILITIES:self.changed.append(canonical)
  web['dateModified']=modified
  for node in nodes:
   if node.get('@type')=='Article':node['dateModified']=modified
  nodes.extend([web,organization,website]);graph={'@context':'https://schema.org','@graph':nodes}
  robots='index,follow' if self.indexable and path not in UTILITIES else 'noindex,follow' if self.indexable else 'noindex,nofollow'
  robots_tag='' if self.indexable and path not in UTILITIES else '<meta name="robots" content="'+robots+'">'
  keywords=[product['sku'],product['shortName']+' '+product['brand'],*product['codes'][1:4]] if product else []
  keyword_tag='<meta name="keywords" content="'+esc(', '.join(dict.fromkeys(keywords)))+'">' if keywords else ''
  verify='<meta name="yandex-verification" content="'+esc(os.environ['YANDEX_VERIFICATION'])+'">' if os.environ.get('YANDEX_VERIFICATION') else ''
  og_type='article' if any(n.get('@type')=='Article' for n in nodes) else 'website'
  article_meta='<meta property="article:modified_time" content="'+modified+'">' if og_type=='article' else ''
  font='/assets/manrope-400.woff2'
  preload='<link rel="preload" href="'+font+'" as="font" type="font/woff2" crossorigin>' if (self.root/'public'/font.lstrip('/')).exists() else ''
  document=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}">{keyword_tag}{robots_tag}<meta name="theme-color" content="#f9dd16"><link rel="canonical" href="{esc(canonical)}">{verify}<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="{og_type}"><meta property="og:site_name" content="СМ ТЕХНО"><meta property="og:image" content="{esc(self.base+primary_image)}"><meta property="og:image:alt" content="{esc(image_alt)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:locale" content="ru_RU">{article_meta}<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{esc(self.base+primary_image)}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">{preload}<link rel="stylesheet" href="/assets/style.css?v={self.asset_versions['style.css']}"><script src="/assets/app.js?v={self.asset_versions['app.js']}" defer></script><script type="application/ld+json">{dump(graph)}</script></head><body>{header}<main id="main">{content}</main>{footer}{cart}<script type="application/json" id="catalog-data">{dump([{k:p[k] for k in ['id','sku','name','price','brand','stockQuantity']} for p in self.products])}</script><noscript><p class="no-js">Каталог и статьи доступны без JavaScript. Для добавления товаров в корзину включите JavaScript в браузере.</p></noscript></body></html>'''
  return document
 def finish(self,paths):
  ns='http://www.sitemaps.org/schemas/sitemap/0.9';image_ns='http://www.google.com/schemas/sitemap-image/1.1';ET.register_namespace('',ns);ET.register_namespace('image',image_ns);root=ET.Element('{'+ns+'}urlset')
  for path in paths:
   if path in UTILITIES:continue
   url=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(url,'{'+ns+'}loc').text=self.base+path;ET.SubElement(url,'{'+ns+'}lastmod').text=self.current[path]['lastmod']
   p=self.byid.get(path.split('/')[2]) if path.startswith('/catalog/') and path.count('/')==3 else None
   if p and p.get('image'):
    image=ET.SubElement(url,'{'+image_ns+'}image');ET.SubElement(image,'{'+image_ns+'}loc').text=self.base+p['image']
    ET.SubElement(image,'{'+image_ns+'}caption').text=self.product_name(p)
  ET.ElementTree(root).write(self.out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
  robots='User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: '+self.base+'/sitemap.xml\n\nUser-agent: Yandex\nAllow: /\nDisallow: /api/\nClean-param: utm_source&utm_medium&utm_campaign&utm_term&utm_content&yclid&gclid&ysclid&fbclid /\nSitemap: '+self.base+'/sitemap.xml\n' if self.indexable else 'User-agent: *\nDisallow: /\n'
  (self.out/'robots.txt').write_text(robots)
  (self.root/'data/seo-state.json').write_text(json.dumps(self.current,ensure_ascii=False,indent=2)+'\n')
  removed=[self.base+p for p in self.previous if p not in self.current and p not in UTILITIES]
  changes_file=self.root/'data/seo-changes.json'
  pending=json.loads(changes_file.read_text()) if changes_file.exists() else {}
  previous_urls=pending.get('urls',[]) if pending.get('origin')==self.base and pending.get('indexable')==self.indexable else []
  urls=list(dict.fromkeys(previous_urls+self.changed+removed))
  changes_file.write_text(json.dumps({'origin':self.base,'indexable':self.indexable,'generated_at':self.now,'urls':urls},ensure_ascii=False,indent=2)+'\n')
  key=os.environ.get('INDEXNOW_KEY','')
  if key:
   if not re.fullmatch('[a-zA-Z0-9-]{8,128}',key):raise ValueError('Invalid INDEXNOW_KEY')
   (self.out/(key+'.txt')).write_text(key)
  if self.commerce.get('yml_enabled'):self.feed()
 def feed(self):
  # Publishing a feed without verified stock would silently imply availability.
  if not self.indexable:raise ValueError('YML requires an indexable production domain')
  items=[p for p in self.products if self.availability(p) is not None and p.get('image')]
  if not items:raise ValueError('YML requires verified availability and actual product images')
  root=ET.Element('yml_catalog',date=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'));shop=ET.SubElement(root,'shop')
  for tag,value in [('name','СМ ТЕХНО'),('company',self.commerce['company'].get('legal_name') or 'СМ ТЕХНО'),('url',self.base+'/')]:ET.SubElement(shop,tag).text=value
  currency=ET.SubElement(shop,'currencies');ET.SubElement(currency,'currency',id='RUR',rate='1')
  categories=ET.SubElement(shop,'categories');cat_ids={k:str(i+1) for i,k in enumerate(self.categories)}
  for cat,identifier in cat_ids.items():ET.SubElement(categories,'category',id=identifier).text=self.categories[cat][0]
  offers=ET.SubElement(shop,'offers')
  for p in items:
   state=self.availability(p);available='true' if state in ['InStock','LimitedAvailability'] else 'false';offer=ET.SubElement(offers,'offer',id=p['id'],available=available)
   for tag,value in [('url',self.base+'/catalog/'+p['id']+'/'),('price',format(Decimal(str(p['price'])),'f')),('currencyId','RUR'),('categoryId',cat_ids[p['category']]),('name',self.product_name(p)),('vendor',p['brand']),('description',p['copy'][0]+' '+p['copy'][1])]:ET.SubElement(offer,tag).text=value
   if p.get('image'):ET.SubElement(offer,'picture').text=self.base+p['image']
   ET.SubElement(offer,'param',name='Артикул').text=p['sku']
  ET.ElementTree(root).write(self.out/'yandex-products.xml',encoding='utf-8',xml_declaration=True)
