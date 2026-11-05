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
 def test_product_feed_is_production_only_and_matches_catalog(self):
  import subprocess,os
  from xml.etree import ElementTree as ET
  self.assertFalse((self.root/'dist/yandex-products.xml').exists())
  result=subprocess.run([sys.executable,'build.py'],cwd=self.root,env={**os.environ,'INDEXABLE':'true','PUBLIC_SITE_URL':'https://engine.cmteh.ru'},capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
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

if __name__=='__main__':unittest.main()
