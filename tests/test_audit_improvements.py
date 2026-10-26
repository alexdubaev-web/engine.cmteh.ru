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
  page=html.fromstring((root/'dist/category/injectors/bosch/index.html').read_text())
  products=json.loads((root/'data/products.json').read_text())
  expected={p['id'] for p in products if p['category']=='injectors' and p['brand']=='Bosch'}
  self.assertEqual(set(page.xpath('//article[contains(@class,"product-card")]/@data-id')),expected)
  graph=json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
  listing=next(x for x in graph if x['@type']=='ItemList')
  self.assertEqual(listing['numberOfItems'],len(expected))
  self.assertEqual(page.xpath('//select[@id="brand-filter"]/option/@value'),['','Bosch'])
  self.assertIn('/category/injectors/bosch/',(root/'dist/sitemap.xml').read_text())
 def test_customer_pages_do_not_show_image_production_notes(self):
  from lxml import html
  for path in (self.root/'dist').rglob('*.html'):
   page=html.fromstring(path.read_text())
   self.assertFalse(page.xpath('//div[@class="photo-credit"]|//figure[@class="article-cover"]/figcaption'),str(path))
   self.assertNotIn('генеративной модели',page.text_content())
   self.assertNotIn('JavaScript',page.text_content())
   for img in page.xpath('//img'):
    self.assertTrue(img.get('alt'))
 def test_inquiry_carries_visible_product_context(self):
  from lxml import html
  page=html.fromstring((self.root/'dist/catalog/0445120075/index.html').read_text())
  form=page.xpath('//form[@data-kind="inquiry"]')[0]
  self.assertEqual(form.get('data-product-id'),'0445120075')
  self.assertIn('0445120075',form.text_content())
  self.assertTrue(page.xpath('//a[@href="mailto:info@cmteh.ru"]'))
 def test_product_feed_is_production_only_and_matches_catalog(self):
  import subprocess,os
  from xml.etree import ElementTree as ET
  self.assertFalse((self.root/'dist/yandex-products.xml').exists())
  result=subprocess.run([sys.executable,'build.py'],cwd=self.root,env={**os.environ,'INDEXABLE':'true','PUBLIC_SITE_URL':'https://engine.cmteh.ru'},capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
  feed=self.root/'dist/yandex-products.xml'
  self.assertTrue(feed.exists(),'production feed must be generated')
  offers=ET.parse(feed).findall('.//offer')
  products=json.loads((self.root/'data/products.json').read_text())
  self.assertEqual({x.get('id') for x in offers},{p['id'] for p in products})
  by_id={p['id']:p for p in products}
  for offer in offers:
   self.assertEqual(float(offer.findtext('price')),by_id[offer.get('id')]['price'])
   self.assertTrue(offer.findtext('picture').startswith('https://engine.cmteh.ru/'))
 def test_saved_stock_remains_valid_until_next_import(self):
  from lxml import html
  page=html.fromstring((self.root/'dist/catalog/0445120075/index.html').read_text())
  graph=json.loads(page.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
  product=next(x for x in graph if x['@type']=='Product')
  stock=json.loads((self.root/'data/stock.json').read_text())['items']['0445120075']['quantity']
  self.assertEqual(product['offers']['availability'],'https://schema.org/InStock')
  self.assertEqual(product['offers']['inventoryLevel']['value'],stock)
  self.assertIn(f'В наличии: {stock} шт.',page.text_content())

if __name__=='__main__':unittest.main()
