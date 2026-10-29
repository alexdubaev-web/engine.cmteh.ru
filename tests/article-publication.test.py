"""Focused regression for the accepted cold-start article publication."""
import json
import os
from pathlib import Path
import subprocess
import sys
from lxml import etree, html
from PIL import Image
from build_fixture import build_fixture

temporary, root = build_fixture()
out = root / 'dist'
new_slug = 'kodirovanie-forsunok-posle-zameny'
new_url = f'/articles/{new_slug}/'
new_article = html.fromstring((out / 'articles' / new_slug / 'index.html').read_text(encoding='utf-8'))
assert new_article.xpath('string(//link[@rel="canonical"]/@href)').endswith(new_url)
new_cover = new_article.xpath('//figure[@class="article-cover"]/img')[0]
assert new_cover.get('src') == '/assets/injector-coding.webp'
new_image = Image.open(out / 'assets' / 'injector-coding.webp')
new_image_format, new_image_size = new_image.format, new_image.size
new_image.close()
assert new_image_format == 'WEBP'
assert (new_cover.get('width'), new_cover.get('height')) == tuple(str(v) for v in new_image_size)
assert new_cover.get('alt') and new_cover.get('alt').startswith('Две дизельные форсунки')
new_graph = json.loads(new_article.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
new_schema = next(node for node in new_graph if node.get('@type') == 'Article')
assert new_schema['datePublished'] == '2026-10-23'
assert new_schema['image']['url'].endswith('/assets/injector-coding.webp')
assert new_article.xpath('string(//meta[@property="article:published_time"]/@content)') == '2026-10-23'
assert new_article.xpath('//time[@datetime="2026-10-23"]/text()') == ['23 октября 2026']
assert 'калибровочный код' in new_article.text_content().lower()
assert 'не означает, что процедура требуется во всех системах' in new_article.text_content()
assert len(new_article.xpath('//a[contains(@href,"delphiautoparts.com")]')) >= 2
assert len(new_article.xpath('//a[contains(@href,"denso-am.eu")]')) >= 2
assert new_article.xpath('//a[@href="/catalog/28272472/"]')
assert new_article.xpath('//a[@href="/catalog/0445120126/"]')
assert new_article.xpath('//a[@href="/articles/podbor-po-artikulu/"]')
assert new_article.xpath('//a[@href="/articles/forsunka-ili-raspylitel/"]')
for sku in ['28272472', '0445120126']:
    product = html.fromstring((out / 'catalog' / sku / 'index.html').read_text(encoding='utf-8'))
    assert product.xpath(f'//section[contains(@class,"product-reading")]//a[@href="{new_url}"]')
assert html.fromstring((out / 'articles' / 'index.html').read_text(encoding='utf-8')).xpath(f'//a[@href="{new_url}"]')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap = etree.parse(str(out / 'sitemap.xml'))
assert sitemap.xpath('//s:loc[contains(text(), $slug)]', namespaces=ns, slug=new_url)
valve_slug = 'klapan-scv-ili-imv-podbor'
valve_url = f'/articles/{valve_slug}/'
valve_article = html.fromstring((out / 'articles' / valve_slug / 'index.html').read_text(encoding='utf-8'))
assert valve_article.xpath('string(//link[@rel="canonical"]/@href)').endswith(valve_url)
valve_cover = valve_article.xpath('//figure[@class="article-cover"]/img')[0]
assert valve_cover.get('src') == '/assets/fuel-valves.webp'
with Image.open(out / 'assets' / 'fuel-valves.webp') as image:
    assert image.format == 'WEBP' and image.size == (1400, 933)
    assert (valve_cover.get('width'), valve_cover.get('height')) == ('1400', '933')
    assert (out / 'assets' / 'fuel-valves.webp').stat().st_size < 200_000
assert valve_cover.get('alt').startswith('Два металлических клапана управления подачей топлива')
assert not valve_article.xpath('//figure[@class="article-cover"]/figcaption')
valve_graph = json.loads(valve_article.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
valve_schema = next(node for node in valve_graph if node.get('@type') == 'Article')
assert valve_schema['datePublished'] == '2026-10-24'
assert valve_article.xpath('string(//meta[@property="article:published_time"]/@content)') == '2026-10-24'
assert valve_article.xpath('string(//meta[@property="og:image"]/@content)').endswith('/assets/fuel-valves.webp')
for domain in ['denso-am.eu', 'delphiautoparts.com', 'wypalaniedpf.pl']:
    assert valve_article.xpath(f'//a[contains(@href,"{domain}")]')
assert valve_article.xpath('//a[@href="/catalog/9109-903/"]')
assert valve_article.xpath('//a[@href="/catalog/dz111136/"]')
assert valve_article.xpath('//a[@href="/articles/podbor-po-artikulu/"]')
assert valve_article.xpath('//a[@href="/articles/tnvd-pered-zakazom/"]')
for sku in ['9109-903', 'dz111136']:
    product = html.fromstring((out / 'catalog' / sku / 'index.html').read_text(encoding='utf-8'))
    assert product.xpath(f'//section[contains(@class,"product-reading")]//a[@href="{valve_url}"]')
assert html.fromstring((out / 'articles' / 'index.html').read_text(encoding='utf-8')).xpath(f'//a[@href="{valve_url}"]')
assert sitemap.xpath('//s:loc[contains(text(), $slug)]', namespaces=ns, slug=valve_url)
water_slug = 'povtornyy-signal-voda-v-toplive'
water_url = f'/articles/{water_slug}/'
water_article = html.fromstring((out / 'articles' / water_slug / 'index.html').read_text(encoding='utf-8'))
assert water_article.xpath('string(//link[@rel="canonical"]/@href)').endswith(water_url)
water_cover = water_article.xpath('//figure[@class="article-cover"]/img')[0]
assert water_cover.get('src') == '/assets/water-fuel.webp'
with Image.open(out / 'assets' / 'water-fuel.webp') as image:
    assert image.format == 'WEBP' and image.size == (1400, 933)
    assert (water_cover.get('width'), water_cover.get('height')) == ('1400', '933')
    assert (out / 'assets' / 'water-fuel.webp').stat().st_size < 200_000
assert water_cover.get('alt').startswith('Дизельный топливный фильтр-сепаратор')
assert not water_article.xpath('//figure[@class="article-cover"]/figcaption')
water_graph = json.loads(water_article.xpath('//script[@type="application/ld+json"]/text()')[0])['@graph']
water_schema = next(node for node in water_graph if node.get('@type') == 'Article')
assert water_schema['datePublished'] == '2026-10-25'
assert water_article.xpath('string(//meta[@property="article:published_time"]/@content)') == '2026-10-25'
assert water_article.xpath('string(//meta[@property="og:image"]/@content)').endswith('/assets/water-fuel.webp')
for domain in ['delphiautoparts.com', 'perkins.com', 'agcopartsandservice.com']:
    assert water_article.xpath(f'//a[contains(@href,"{domain}")]')
for href in ['/catalog/28272472/', '/catalog/0445120126/', '/category/injectors/',
             '/articles/dizel-ploho-zavoditsya-na-holodnuyu/', '/articles/tnvd-pered-zakazom/']:
    assert water_article.xpath(f'//a[@href="{href}"]')
for sku in ['28272472', '0445120126']:
    product = html.fromstring((out / 'catalog' / sku / 'index.html').read_text(encoding='utf-8'))
    assert product.xpath(f'//section[contains(@class,"product-reading")]//a[@href="{water_url}"]')
assert html.fromstring((out / 'articles' / 'index.html').read_text(encoding='utf-8')).xpath(f'//a[@href="{water_url}"]')
assert sitemap.xpath('//s:loc[contains(text(), $slug)]', namespaces=ns, slug=water_url)
articles_source = root / 'data' / 'articles.py'
articles_text = articles_source.read_text(encoding='utf-8')
articles_source.write_text(articles_text.replace("'products':['9109-903','DZ111136']", "'products':['UNKNOWN-SKU','DZ111136']", 1), encoding='utf-8')
invalid_build = subprocess.run([sys.executable, 'build.py'], cwd=root, env={**os.environ, 'INDEXABLE': 'false', 'PUBLIC_SITE_URL': ''}, capture_output=True, text=True)
assert invalid_build.returncode != 0 and 'unknown or ambiguous catalog SKU: UNKNOWN-SKU' in invalid_build.stderr
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
assert not article.xpath('//figure[@class="article-cover"]/figcaption')
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
assert html.fromstring((out / 'articles' / 'index.html').read_text(encoding='utf-8')).xpath(f'//a[@href="{url}"]')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap = etree.parse(str(out / 'sitemap.xml'))
assert sitemap.xpath('//s:loc[contains(text(), $slug)]', namespaces=ns, slug=url)
unit_slug = 'nasos-forsunka-i-common-rail'
unit_url = f'/articles/{unit_slug}/'
unit_article = html.fromstring((out / 'articles' / unit_slug / 'index.html').read_text(encoding='utf-8'))
assert unit_article.xpath('string(//link[@rel="canonical"]/@href)').endswith(unit_url)
assert unit_article.xpath('string(//meta[@property="article:published_time"]/@content)') == '2026-10-26'
assert unit_article.xpath('//time[@datetime="2026-10-26"]')
unit_cover = unit_article.xpath('//figure[@class="article-cover"]/img')[0]
assert unit_cover.get('src') == '/assets/unit-injector.webp'
with Image.open(out / 'assets' / 'unit-injector.webp') as image:
    assert image.format == 'WEBP' and image.size == (1399, 933)
    assert (out / 'assets' / 'unit-injector.webp').stat().st_size < 200_000
    assert (unit_cover.get('width'), unit_cover.get('height')) == ('1399', '933')
assert unit_cover.get('alt') and 'условная' in unit_cover.get('alt').lower()
assert not unit_article.xpath('//figure[@class="article-cover"]/figcaption')
for domain in ['bosch-mobility.com', 'boschaftermarket.com']:
    assert unit_article.xpath(f'//a[contains(@href,"{domain}")]')
for href in ['/catalog/0414701072/', '/catalog/0445120075/', '/category/injectors/',
             '/articles/podbor-po-artikulu/', '/articles/forsunka-ili-raspylitel/']:
    assert unit_article.xpath(f'//a[@href="{href}"]')
for sku in ['0414701072', '0445120075']:
    product = html.fromstring((out / 'catalog' / sku / 'index.html').read_text(encoding='utf-8'))
    assert product.xpath(f'//section[contains(@class,"product-reading")]//a[@href="{unit_url}"]')
for listing in [out / 'index.html', out / 'articles' / 'index.html']:
    assert html.fromstring(listing.read_text(encoding='utf-8')).xpath(f'//a[@href="{unit_url}"]')
assert sitemap.xpath('//s:loc[contains(text(), $slug)]', namespaces=ns, slug=unit_url)
temporary.cleanup()
print('PASS article publication: cover, citations, schema/OG, listing, sitemap, reciprocal product links, and legacy articles')
