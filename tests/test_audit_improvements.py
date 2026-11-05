import unittest,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
class GeneratedFlowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from build_fixture import build_fixture
  cls.fixture,cls.root=build_fixture()
 @classmethod
 def tearDownClass(cls):cls.fixture.cleanup()
 def test_landing_has_exact_bosch_injector_assortment_and_schema(self):
  from lxml import html
  root=self.root
  page=html.fromstring((root/'dist/category/injectors/bosch/index.html').read_text(encoding='utf-8'))
  products=json.loads((root/'data/products.json').read_text(encoding='utf-8'))
  expected={p['id'] for p in products if p['category']=='injectors' and p['brand']=='Bosch'}
  self.assertEqual(set(page.xpath('//article[contains(@class,"product-card")]/@data-id')),expected)
  graph=json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
  listing=next(x for x in graph if x['@type']=='ItemList')
  self.assertEqual(listing['numberOfItems'],len(expected))
  self.assertEqual(page.xpath('//select[@id="brand-filter"]/option/@value'),['','Bosch'])
  self.assertIn('/category/injectors/bosch/',(root/'dist/sitemap.xml').read_text(encoding='utf-8'))
 def test_item_lists_follow_rendered_product_card_order(self):
  from lxml import html
  checked_pages=0
  for path in (self.root/'dist').rglob('*.html'):
   page=html.fromstring(path.read_text(encoding='utf-8'))
   if not page.xpath('//nav[@class="tabs"]'):
    continue
   card_ids=page.xpath('//article[contains(concat(" ",normalize-space(@class)," ")," product-card ")]/@data-id')
   if not card_ids:
    continue
   graph=json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
   lists=[node for node in graph if node.get('@type')=='ItemList']
   self.assertEqual(len(lists),1,str(path))
   schema_ids=[entry['url'].rsplit('/',2)[-2] for entry in lists[0]['itemListElement']]
   self.assertEqual(schema_ids,card_ids,str(path))
   self.assertEqual([entry['position'] for entry in lists[0]['itemListElement']],list(range(1,len(card_ids)+1)),str(path))
   checked_pages+=1
  self.assertGreaterEqual(checked_pages,10)
 def test_catalog_tabs_and_honeypot_keep_accessible_structure(self):
  from lxml import html
  page=html.fromstring((self.root/'dist/catalog/index.html').read_text(encoding='utf-8'))
  self.assertEqual(len(page.xpath('//nav[@class="tabs"][@aria-label="Категории запчастей"]')),1)
  self.assertEqual(page.xpath('//div[@class="trap"][@aria-hidden="true"]/label/input[@name="website"][@tabindex="-1"]/@autocomplete'),['off','off'])
  self.assertFalse(page.xpath('//label[@aria-hidden="true"]'))
 def test_selected_product_copy_and_reviewed_article_keep_public_metadata_truthful(self):
  from lxml import html
  records=json.loads((self.root/'data/product_technical.json').read_text(encoding='utf-8'))
  for sku in ('0445020089','5620004100','DZ10599'):
   with self.subTest(sku=sku):
    page=html.fromstring((self.root/'dist/catalog'/sku.lower()/'index.html').read_text(encoding='utf-8'))
    description=page.xpath('//div[@itemprop="description"]')[0]
    self.assertEqual(description.xpath('./p/text()'),[p['text'] for p in records[sku]['overview']])
    self.assertTrue(page.xpath('string(//meta[@name="description"]/@content)').startswith(sku+' '))
    self.assertIn('Цена с НДС.',page.xpath('string(//meta[@name="description"]/@content)'))
  target=html.fromstring((self.root/'dist/articles/forsunka-ili-raspylitel/index.html').read_text(encoding='utf-8'))
  article=next(node for node in json.loads(target.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph'] if node.get('@type')=='Article')
  self.assertNotIn('datePublished',article)
  self.assertEqual(article['dateModified'],'2026-11-05')
  self.assertEqual(target.xpath('string(//time[@class="article-reviewed"]/@datetime)'),'2026-11-05')
  self.assertEqual(len(target.xpath('//h1')),1)
  for path in (self.root/'dist/articles').glob('*/index.html'):
   page=html.fromstring(path.read_text(encoding='utf-8'))
   self.assertTrue(page.xpath('//div[contains(@class,"article-meta")]/span/a[@href="/about/"][normalize-space(.)="Материал подготовлен СМ ТЕХНО"]'),str(path))
 def test_customer_pages_do_not_show_image_production_notes(self):
  from lxml import html
  for path in (self.root/'dist').rglob('*.html'):
   page=html.fromstring(path.read_text(encoding='utf-8'))
   self.assertFalse(page.xpath('//div[@class="photo-credit"]|//figure[@class="article-cover"]/figcaption'),str(path))
   self.assertNotIn('генеративной модели',page.text_content())
   self.assertNotIn('JavaScript',page.text_content())
   for img in page.xpath('//img'):
    self.assertTrue(img.get('alt'))
 def test_inquiry_carries_visible_product_context(self):
  from lxml import html
  products=json.loads((self.root/'data/products.json').read_text(encoding='utf-8'))
  for product in products:
   with self.subTest(sku=product['sku']):
    page=html.fromstring((self.root/'dist/catalog'/product['id']/'index.html').read_text(encoding='utf-8'))
    form=page.xpath('//form[@data-kind="inquiry"]')[0]
    self.assertEqual(form.get('data-product-id'),product['id'])
    self.assertIn(product['sku'],form.text_content())
    self.assertIn(product['sku'],form.xpath('.//textarea[@name="comment"]/@placeholder')[0])
    self.assertTrue(page.xpath('//a[@href="mailto:info@cmteh.ru"]'))
 def test_sku_first_names_match_pages_lists_cart_and_backend(self):
  from lxml import html
  products=json.loads((self.root/'data/products.json').read_text(encoding='utf-8'))
  backend={p['id']:p for p in json.loads((self.root/'backend/catalog.json').read_text(encoding='utf-8'))}
  catalog=html.fromstring((self.root/'dist/catalog/index.html').read_text(encoding='utf-8'))
  payload={p['id']:p for p in json.loads(catalog.xpath('//script[@id="catalog-data"]/text()')[0])}
  for product in products:
   with self.subTest(sku=product['sku']):
    page=html.fromstring((self.root/'dist/catalog'/product['id']/'index.html').read_text(encoding='utf-8'))
    name=page.xpath('string(//h1)')
    self.assertTrue(name.startswith(product['sku']+' '),name)
    self.assertEqual(name.count(product['sku']),1)
    self.assertIn(product['shortName'],name)
    schema=next(n for n in json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph'] if n['@type']=='Product')
    self.assertEqual(schema['name'],name)
    self.assertEqual(schema['mpn'],product['sku'])
    self.assertEqual(payload[product['id']]['name'],name)
    self.assertEqual(backend[product['id']]['name'],name)
    self.assertEqual(backend[product['id']]['price'],product['price'])
    card=catalog.xpath('//article[@data-id=$id]',id=product['id'])[0]
    self.assertEqual(card.xpath('string(.//a[@class="product-name"])'),name)
    self.assertEqual(card.text_content().count(product['sku']),1)
    self.assertTrue(page.xpath('string(//title)').startswith(product['sku']+' '))
    self.assertIn('купить',page.xpath('string(//title)'))
    self.assertTrue(page.xpath('string(//meta[@name="description"]/@content)').startswith(product['sku']+' '))
    fragment_ids=set(page.xpath('//@id'))
    for href in page.xpath('//nav[@class="product-anchor-nav"]/@href'):
     self.assertIn(href[1:],fragment_ids,'product navigation must point to rendered content')
    self.assertFalse(page.xpath('//ul[contains(@class,"buying-checklist")]'))
    self.assertTrue(page.xpath('//*[@id="fitment"]//a[@href="#selection"]'))
    self.assertFalse(page.xpath('//section[@id="part-numbers"]//h2[contains(.,"Номера для сверки")]'))
 def test_product_feed_is_production_only_and_matches_catalog(self):
  import subprocess,os
  from xml.etree import ElementTree as ET
  self.assertFalse((self.root/'dist/yandex-products.xml').exists())
  result=subprocess.run([sys.executable,'build.py'],cwd=self.root,env={**os.environ,'INDEXABLE':'true','PUBLIC_SITE_URL':'https://engine.cmteh.ru'},capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
  from lxml import html
  home=html.fromstring((self.root/'dist/index.html').read_text(encoding='utf-8'))
  module_scripts=home.xpath('//script[@type="module" and contains(@src,"analytics.js")]')
  self.assertEqual(len(module_scripts),1)
  self.assertIsNone(module_scripts[0].get('defer'))
  feed=self.root/'dist/yandex-products.xml'
  self.assertTrue(feed.exists(),'production feed must be generated')
  from datetime import datetime,timezone,timedelta
  feed_root=ET.parse(feed).getroot()
  generated_at=datetime.fromisoformat(feed_root.attrib['date'])
  self.assertIsNotNone(generated_at.utcoffset(),'YML date must include its timezone')
  self.assertLess(abs(datetime.now(timezone.utc)-generated_at),timedelta(minutes=5))
  offers=feed_root.findall('.//offer')
  products=json.loads((self.root/'data/products.json').read_text(encoding='utf-8'))
  self.assertEqual({x.get('id') for x in offers},{p['id'] for p in products})
  by_id={p['id']:p for p in products}
  for offer in offers:
   self.assertEqual(float(offer.findtext('price')),by_id[offer.get('id')]['price'])
   self.assertTrue(offer.findtext('picture').startswith('https://engine.cmteh.ru/'))
   self.assertEqual(offer.findtext('vendorCode'),by_id[offer.get('id')]['sku'])
   self.assertTrue(offer.findtext('name').startswith(by_id[offer.get('id')]['sku']+' '))
 def test_saved_stock_remains_valid_until_next_import(self):
  from lxml import html
  page=html.fromstring((self.root/'dist/catalog/0445120075/index.html').read_text(encoding='utf-8'))
  graph=json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
  product=next(x for x in graph if x['@type']=='Product')
  stock=json.loads((self.root/'data/stock.json').read_text(encoding='utf-8'))['items']['0445120075']['quantity']
  self.assertEqual(product['offers']['availability'],'https://schema.org/InStock')
  self.assertEqual(product['offers']['inventoryLevel']['value'],stock)
  self.assertIn(f'В наличии: {stock} шт.',page.text_content())
 def test_structured_overview_and_kit_render_consistently_across_html_schema_and_feed(self):
  import os,subprocess
  from xml.etree import ElementTree as ET
  from build_fixture import build_fixture
  fixture,root=build_fixture()
  try:
   data_path=root/'data/product_technical.json';records=json.loads(data_path.read_text(encoding='utf-8'));record=records['RE539764']
   source=record['sources'][0]['url']
   overview=[{'text':'Overview first <part> & details.','source_urls':[source],'evidence':'A'},{'text':'Second technical paragraph.','source_urls':[source],'evidence':'B'},{'text':'Third paragraph, not truncated.','source_urls':[source],'evidence':'A'}]
   record['overview']=overview
   used_sources={source}|{fact['source_url'] for fact in record['facts']}
   record['sources']=[item for item in record['sources'] if item['url'] in used_sources]
   record['sections']=[{'id':'compatibility','title':'Применимость по каталогу производителя','paragraphs':[{'text':'Examples include Model 1 and Model 2.','source_urls':[source],'evidence':'A'}],'models':[f'Model {i}' for i in range(1,160)],'model_source_urls':[source],'model_evidence':'A'}]
   record['kit_contents']={'title':'Каталожный состав комплекта','intro':[{'text':'Five listed components.','source_urls':[source],'evidence':'A'}],'groups':[{'title':'Main group','items':[{'position':str(i),'part_number':f'PN-{i}','name':f'Component {i}','quantity':None if i==5 else i,'note':'Check fit <before> order' if i==1 else '','source_urls':[source],'evidence':'A'} for i in range(1,6)]}],'notes':[]}
   data_path.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
   env={**os.environ,'INDEXABLE':'true','PUBLIC_SITE_URL':'https://engine.cmteh.ru','INDEXNOW_KEY':''}
   result=subprocess.run([sys.executable,'build.py'],cwd=root,env=env,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   from lxml import html
   page=html.fromstring((root/'dist/catalog/re539764/index.html').read_text(encoding='utf-8'))
   overview_node=page.xpath('//div[@itemprop="description"]')[0]
   self.assertEqual(overview_node.xpath('./p/text()'),[item['text'] for item in overview])
   self.assertIn('&lt;part&gt; &amp; details',html.tostring(overview_node,encoding='unicode'))
   self.assertEqual(len(page.xpath('//table[contains(@class,"product-spec-table")]//tbody/tr')),5)
   self.assertEqual(page.xpath('string(//details[@class="product-models-details"]/summary)'),'Все модели из каталога производителя (159)')
   self.assertEqual(len(page.xpath('//ul[@class="product-models"]/li')),159)
   self.assertEqual(page.xpath('string(//table[contains(@class,"product-spec-table")]//tbody/tr[5]/td[4])'),'')
   self.assertIn('Check fit <before> order',page.text_content())
   graph=json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
   product=next(node for node in graph if node.get('@type')=='Product')
   expected=' '.join(item['text'] for item in overview)
   self.assertEqual(product['description'],expected)
   self.assertEqual(len(product['additionalProperty']),len(record['facts']))
   self.assertNotIn('Номер для проверки',[item['name'] for item in product['additionalProperty']])
   offer=ET.parse(root/'dist/yandex-products.xml').find('.//offer[@id="re539764"]')
   self.assertIsNotNone(offer)
   self.assertEqual(offer.findtext('description'),expected)
  finally:fixture.cleanup()
 def test_catalogue_composition_and_injector_kit_classification(self):
  from lxml import html
  page=html.fromstring((self.root/'dist/catalog/dz10599/index.html').read_text(encoding='utf-8'))
  rows=page.xpath('//section[@id="kit-contents"]//tbody/tr')
  self.assertEqual(len(rows),49)
  by_number={row.xpath('string(td[2])'):row for row in rows}
  for number,quantity in [('DZ10211','6'),('RE529319','6'),('RE529318','6'),('RE529320','1'),('R519287','14'),('RE529187','24')]:
   self.assertEqual(by_number[number].xpath('string(td[4])'),quantity)
  self.assertIn('не следует прибавлять',page.xpath('string(//section[@id="kit-contents"])'))
  self.assertIn('R519427',page.text_content())
  self.assertIn('6 × DZ10211',page.xpath('string(//meta[@name="description"]/@content)'))
  products=json.loads((self.root/'data/products.json').read_text(encoding='utf-8'))
  for sku in ('DZ112112','DZ100218'):
   product=next(p for p in products if p['sku']==sku)
   self.assertEqual(product['category'],'injectors')
   product_page=html.fromstring((self.root/'dist/catalog'/product['id']/'index.html').read_text(encoding='utf-8'))
   self.assertIn('комплект топливной форсунки',product_page.xpath('string(//h1)').lower())
 def test_invalid_new_evidence_cannot_be_published(self):
  import os,subprocess
  from build_fixture import build_fixture
  for failure in ('missing_source','evidence_c'):
   with self.subTest(failure=failure):
    fixture,root=build_fixture()
    try:
     path=root/'data/product_technical.json';records=json.loads(path.read_text(encoding='utf-8'));record=records['RE539764']
     text={'text':'Invalid fixture-only statement.','source_urls':['https://not-in-source-list.example/item'],'evidence':'A'}
     if failure=='evidence_c':text={'text':'Invalid evidence label.','source_urls':[record['sources'][0]['url']],'evidence':'C'}
     record['overview']=[text];path.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
     result=subprocess.run([sys.executable,'build.py'],cwd=root,env={**os.environ,'INDEXABLE':'false','PUBLIC_SITE_URL':''},capture_output=True,text=True)
     self.assertNotEqual(result.returncode,0)
     old_page=(root/'dist/catalog/re539764/index.html').read_text(encoding='utf-8')
     self.assertNotIn('Invalid fixture-only statement',old_page)
     self.assertNotIn('Invalid evidence label',old_page)
    finally:fixture.cleanup()

if __name__=='__main__':unittest.main()
