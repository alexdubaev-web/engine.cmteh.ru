"""Focused regression for the accepted cold-start article publication."""
import json
from pathlib import Path
from lxml import etree, html
from PIL import Image
from build_fixture import build_fixture

temporary, root = build_fixture()
out = root / 'dist'
slug = 'dizel-ploho-zavoditsya-na-holodnuyu'
url = f'/articles/{slug}/'
article = html.fromstring((out / 'articles' / slug / 'index.html').read_text(encoding='utf-8'))
assert article.xpath('string(//link[@rel="canonical"]/@href)').endswith(url)
assert article.xpath('string(//meta[@name="robots"]/@content)') == 'noindex,nofollow'
cover = article.xpath('//figure[@class="article-cover"]/img')[0]
assert cover.get('src') == '/assets/cold-start.webp'
image = Image.open(out / 'assets/cold-start.webp')
image_format, image_size = image.format, image.size
image.close()
assert image_format == 'WEBP'
assert (cover.get('width'), cover.get('height')) == tuple(str(v) for v in image_size)
assert bool(cover.get('alt')) and (out / 'assets/cold-start.webp').stat().st_size < 200_000
assert cover.get('alt').startswith('Топливный фильтр')
assert 'Иллюстрация создана с помощью генеративной модели' in article.xpath('string(//figure[@class="article-cover"]/figcaption)')
graph = json.loads(article.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
schema = next(node for node in graph if node.get('@type') == 'Article')
assert schema['datePublished'] == '2026-10-22'
assert schema['image']['url'].endswith('/assets/cold-start.webp')
assert article.xpath('string(//meta[@property="og:image"]/@content)').endswith('/assets/cold-start.webp')
assert article.xpath('string(//meta[@property="article:published_time"]/@content)') == '2026-10-22'
assert article.xpath('//time[@datetime="2026-10-22"]/text()') == ['22 октября 2026']
assert len(article.xpath('//a[contains(@href,"perkins.com")]')) >= 2
assert article.xpath('//a[starts-with(@href,"https://") and contains(@href,"delphiautoparts.com")]')
assert 'Не ослабляйте соединения высокого давления' in article.text_content()
diagnosis = article.xpath('//section[h2[contains(normalize-space(),"Передайте сервису исходные данные")]]')[0]
assert [len(items.xpath('./li')) for items in diagnosis.xpath('./ul')] == [3, 2]
assert not article.xpath('//article[contains(@class,"read-content")]//p[normalize-space()=$lead]', lead=article.xpath('string(//p[@class="lead"])') )
assert article.xpath('//section//h3[normalize-space()="Когда диагноз подтверждён"]')
assert len(article.xpath('//section[@class="article-products"]//a[starts-with(@href,"/catalog/")]')) == 2
for sku in ['0445120075', '0445120072']:
    product = html.fromstring((out / 'catalog' / sku / 'index.html').read_text(encoding='utf-8'))
    assert product.xpath(f'//section[contains(@class,"product-reading")]//a[@href="{url}"]')
    assert len(product.xpath('//section[contains(@class,"product-reading")]//article[contains(@class,"article-card")]')) <= 2
for old_slug in ['podbor-po-artikulu', 'tnvd-pered-zakazom', 'forsunka-ili-raspylitel', 'spisok-zapchastey-dlya-zakaza']:
    assert (out / 'articles' / old_slug / 'index.html').is_file()
    assert html.fromstring((out / 'articles' / old_slug / 'index.html').read_text(encoding='utf-8')).xpath('//h1')
for listing in [out / 'index.html', out / 'articles' / 'index.html']:
    assert html.fromstring(listing.read_text(encoding='utf-8')).xpath(f'//a[@href="{url}"]')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap = etree.parse(str(out / 'sitemap.xml'))
assert sitemap.xpath('//s:loc[contains(text(), $slug)]', namespaces=ns, slug=url)
temporary.cleanup()
print('PASS article publication: cover, citations, schema/OG, listing, sitemap, reciprocal product links, and legacy articles')
