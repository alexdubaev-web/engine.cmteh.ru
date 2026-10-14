from pathlib import Path
import sys,json,html,re,os,shutil,mimetypes,base64
from urllib.parse import quote,urlsplit
sys.path.insert(0,str(Path(__file__).parent/'data'))
from product_copy import COPY
from seo import SEO, breadcrumbs, money, AVAILABILITY
from articles import ARTICLES
from pipeline_io import pipeline_lock,publish_files
import tempfile

ROOT=Path(__file__).parent
with pipeline_lock(ROOT):
 stage_context=tempfile.TemporaryDirectory(prefix='.build-stage-',dir=ROOT)
 stage=Path(stage_context.name)
 OUT=stage/'dist'
 OUT.mkdir()
 shutil.copytree(ROOT/'public/assets',OUT/'assets')
 P=json.loads((ROOT/'data/products.json').read_text(encoding='utf-8'))
 TECHNICAL=json.loads((ROOT/'data/product_technical.json').read_text(encoding='utf-8')) if (ROOT/'data/product_technical.json').exists() else {}
 if TECHNICAL and set(TECHNICAL)!={p['sku'] for p in P}:raise ValueError('Technical records must cover every catalog SKU exactly once')
 for sku,record in TECHNICAL.items():
  sources=record.get('sources',[]);source_indices={source['url']:i for i,source in enumerate(sources,1)}
  if len(source_indices)!=len(sources):raise ValueError(f'Duplicate technical source for {sku}')
  if any(urlsplit(source['url']).scheme!='https' or not urlsplit(source['url']).netloc for source in sources):raise ValueError(f'Non-HTTPS technical source for {sku}')
  if any(fact.get('source_url') not in source_indices for fact in record.get('facts',[])):raise ValueError(f'Missing technical source association for {sku}')
  if {fact['source_url'] for fact in record.get('facts',[])}!=set(source_indices):raise ValueError(f'Unused technical source for {sku}')
  if not record.get('facts') and sources:raise ValueError(f'Sources without published facts for {sku}')
 STOCK=json.loads((ROOT/'data/stock.json').read_text(encoding='utf-8')).get('items',{}) if (ROOT/'data/stock.json').exists() else {}
 for p in P:p['stockQuantity']=STOCK.get(p['id'],{}).get('quantity')
 images={x['id']:x for x in json.loads((ROOT/'data/images.json').read_text(encoding='utf-8'))} if (ROOT/'data/images.json').exists() else {}
 for p in P:p.update(images.get(p['id'],{}));p['copy']=COPY[p['sku']];p['note']=p['copy'][0]
 origin=os.environ.get('PUBLIC_SITE_URL','').rstrip('/')
 indexable=os.environ.get('INDEXABLE','false')=='true' and bool(re.fullmatch(r'https://[a-zA-Z0-9.-]+(?::\d+)?',origin))
 analytics_enabled=indexable and origin=='https://engine.cmteh.ru'
 if origin and not re.fullmatch(r'https://[a-zA-Z0-9.-]+(?::\d+)?',origin):raise ValueError('PUBLIC_SITE_URL must be an HTTPS origin without a path')
 preview='https://cm-techno-diesel.alexdubaev.chatgpt.site'
 base=origin or preview
 CATS={'injectors':('Форсунки','Топливные форсунки Bosch, Delphi и Denso','Форсунки Common Rail и насос-форсунки. Подберите деталь по артикулу и данным двигателя.'),'pumps':('ТНВД','Топливные насосы высокого давления','ТНВД Bosch, Delphi, Denso и John Deere. Сверьте полный номер и исполнение насоса.'),'nozzles':('Распылители','Распылители и комплекты распылителей','Распылители для форсунок Bosch, Delphi и John Deere. Перед заказом проверьте номер и состав комплекта.'),'valves':('Клапаны','Клапаны топливной системы','Электромагнитные клапаны, регуляторы подачи SCV и давления HPV. Для подбора понадобится номер клапана и узла.'),'other':('Другие запчасти','Компоненты топливной системы и двигателя','Топливные рампы, подкачивающие насосы, блоки управления и ремонтные комплекты. Уточните исполнение и состав набора перед заказом.')}
 BRANDS={'bosch':'Bosch','delphi':'Delphi','denso':'Denso','john-deere':'John Deere','vdo':'VDO / Vitesco (Aumovio)'}
 def e(s):return html.escape(str(s),quote=True)
 def js(o):return json.dumps(o,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 def document(path):
  source=(ROOT/'docs'/path).read_text(encoding='utf-8').splitlines()
  blocks=[]; paragraph=[]
  def flush():
   if paragraph:
    text=' '.join(paragraph)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{e(m.group(2))}"'+(' target="_blank" rel="noopener"' if m.group(2).startswith('https://') else '')+f'>{e(m.group(1))}</a>',text)
    blocks.append('<p>'+text+'</p>');paragraph.clear()
  for line in source:
   if line.startswith('# '):flush()
   elif line.startswith('## '):flush();blocks.append('<h2>'+e(line[3:])+'</h2>')
   elif not line.strip():flush()
   else:paragraph.append(line.replace('**',''))
  flush();return '<div class="wrap read-content">'+''.join(blocks)+'</div>'
 def icon(name):
  paths={'arrow':'<path d="M4 12h16m-6-6 6 6-6 6"/>','down':'<path d="M12 4v16m-6-6 6 6 6-6"/>','plus':'<path d="M12 5v14M5 12h14"/>','search':'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>','bag':'<path d="M5 7h14l1 14H4L5 7Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>','menu':'<path d="M4 7h16M4 12h16M4 17h16"/>','part':'<path d="m8 3 8 0 3 5-3 5H8L5 8l3-5ZM9 13v7h6v-7M5 8h14"/><circle cx="12" cy="8" r="2"/>','document':'<path d="M6 3h9l4 4v14H6V3Zm9 0v5h4M9 12h7M9 16h5"/>'}
  return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>'
 DIMENSIONS=json.loads((ROOT/'data/image-dimensions.json').read_text(encoding='utf-8'))
 seo=SEO(ROOT,OUT,base,indexable,P,CATS)
 seo.state_root=stage/'data'
 seo.state_root.mkdir()
 if (ROOT/'data/seo-changes.json').exists():shutil.copy2(ROOT/'data/seo-changes.json',seo.state_root/'seo-changes.json')
 def picture(p,detail=False):
  if not p.get('image'):return f'<div class="placeholder">{icon("part")}<small>Фото уточняется</small></div>'
  width,height=DIMENSIONS[p['image']]
  alt=seo.product_name(p)
  props='loading="eager" fetchpriority="high" itemprop="image"' if detail else 'loading="lazy"'
  return f'<img src="{p["image"]}" alt="{e(alt)}" title="{e(alt)}" width="{width}" height="{height}" {props} decoding="async">'
 def stock_label(p):
  state=seo.availability(p)
  if not state:return ''
  label=AVAILABILITY[state]
  if p.get('stockQuantity') is not None:label+=': '+str(p['stockQuantity'])+' шт.'
  return f'<div class="stock-badge">{e(label)}</div>'
 def technical_section(p):
  record=TECHNICAL.get(p['sku'])
  if not record or not record.get('facts'):return ''
  facts=''.join(f'<div><dt>{e(fact["label"])}</dt><dd>{e(fact["value"])}</dd></div>' for fact in record.get('facts',[]))
  fact_list='<dl class="specs">'+facts+'</dl>' if facts else ''
  return f'<section class="product-description" id="technical"><h2>Технические данные</h2><div>{fact_list}</div></section>'
 def product_description(p):
  text=p['copy'][2]
  if p.get('stockQuantity') is not None:text+=' В наличии: '+str(p['stockQuantity'])+' шт.'
  return text
 def card(p):
  return f'''<article class="product-card" data-id="{p['id']}" data-category="{p['category']}" data-brand="{e(p['brand'])}" data-price="{p['price']}" data-search="{e(' '.join(p['codes'])+' '+p['name']+' '+p['brand'])}"><a class="product-image" href="/catalog/{p['id']}/" aria-label="{e(p['name']+' '+p['sku'])}">{picture(p)}</a><div class="product-info"><div class="brand-label">{e(p['brand'])}</div>{stock_label(p)}<a href="/catalog/{p['id']}/" class="sku">{e(p['sku'])}</a><a href="/catalog/{p['id']}/" class="product-name">{e(p['shortName'])}</a><div class="product-bottom"><div class="price">{money(p['price'])} ₽</div><div class="product-actions"><button class="btn small" data-add="{p['id']}" aria-label="Добавить {e(p['sku'])} в корзину">{icon('plus')} В корзину</button><a class="detail-link" href="/catalog/{p['id']}/">Подробнее {icon("arrow")}</a></div></div></div></article>'''
 def form(kind):
  return f'''<form class="form order-form ym-hide-content" data-kind="{kind}"><label>Имя<input class="ym-disable-keys" name="name" autocomplete="name" placeholder="Как к вам обращаться" minlength="2" maxlength="100" required></label><label>Телефон или email<input class="ym-disable-keys" name="contact" autocomplete="email" placeholder="Для ответа" maxlength="160" required></label><label class="full">Артикулы и данные техники<textarea class="ym-disable-keys" name="comment" maxlength="5000" placeholder="Например: форсунка 0445120075, 2 шт.; модель двигателя…"></textarea></label><label class="trap" aria-hidden="true">Не заполняйте это поле<input name="website" tabindex="-1" autocomplete="off"></label><label class="consent full"><input type="checkbox" name="consent" required><input type="hidden" name="consentVersion" value="2026-10-06"><span>Согласен на <a href="/consent/" target="_blank" rel="noopener">обработку персональных данных</a> для ответа на обращение. <a href="/privacy/" target="_blank" rel="noopener">Политика обработки данных</a></span></label><button class="btn full" type="submit">Отправить запрос {icon('arrow')}</button><div class="form-status full" role="status" aria-live="polite"></div><button class="export-button full" type="button" data-export hidden>Сохранить список в файл</button></form>'''
 HEADER=f'''<a class="skip" href="#main">Перейти к содержанию</a><header class="header"><div class="wrap header-inner"><a href="/" class="logo" aria-label="СМ ТЕХНО - главная"><img src="/assets/logo.webp" alt="СМ ТЕХНО - запчасти для спецтехники" width="200" height="74"></a><nav class="nav" id="navigation" aria-label="Основная навигация"><a href="/catalog/">Каталог</a><a href="/#selection">Подбор запчастей</a><a href="/#how-to-order">Как заказать</a><a href="/delivery/">Доставка и оплата</a><a href="/articles/">Статьи</a><a href="/about/">О компании</a><a href="/contacts/">Контакты</a></nav><button class="btn outline cart-button" data-cart-open>{icon('bag')} Корзина <span class="count" data-cart-count>0</span></button><button class="menu-toggle" aria-label="Открыть меню" aria-expanded="false" aria-controls="navigation">{icon('menu')}</button></div></header>'''
 FOOTER='''<footer class="footer"><div class="wrap"><div class="footer-top"><div class="footer-brand"><a href="/"><img src="/assets/logo.webp" alt="СМ ТЕХНО" width="180" height="66" loading="lazy"></a><p>Запчасти для дизельной техники.<br>Подбор по артикулу. Продажи по всей России.</p></div><nav class="footer-nav" aria-label="Каталог в подвале"><strong>Каталог</strong><a href="/catalog/">Весь каталог</a><a href="/category/injectors/">Топливные форсунки</a><a href="/category/pumps/">Насосы высокого давления</a><a href="/category/nozzles/">Распылители</a><a href="/category/valves/">Клапаны</a></nav><nav class="footer-nav" aria-label="Информация"><strong>Покупателям</strong><a href="/#how-to-order">Как заказать</a><a href="/delivery/">Доставка и оплата</a><a href="/articles/">Статьи</a><a href="/#selection">Подбор запчастей</a><a href="/about/">О компании</a><a href="/contacts/">Контакты</a></nav></div><div class="footer-bottom"><span>© 2026 СМ ТЕХНО</span><span>Названия производителей и артикулы используются для идентификации запчастей.</span><a href="/privacy/">Обработка данных</a>'''+('<button class="analytics-preferences" type="button" data-analytics-preferences>Настройки аналитики</button>' if analytics_enabled else '')+'''</div></div></footer>'''
 CART=f'''<dialog id="cart-dialog" aria-labelledby="cart-title"><div class="dialog-head"><h2 id="cart-title">Ваша корзина</h2><button class="close" data-cart-close aria-label="Закрыть корзину">×</button></div><div class="dialog-body"><div id="cart-items"></div><div id="cart-totals"></div><button class="export-button" data-export type="button">Сохранить список в файл</button>{form('cart')}</div></dialog><div class="toast" role="status" aria-live="polite"></div>'''
 paths=[]
 def page(path,title,description,content,schema=None):
  document=seo.render(path,title,description,content,schema,HEADER,FOOTER,CART,analytics_enabled)
  target=OUT/(path.strip('/')+'/index.html' if path!='/' else 'index.html');target.parent.mkdir(parents=True,exist_ok=True);target.write_text(document,encoding='utf-8');paths.append(path)
 def crumbs(items):return breadcrumbs(items)
 def catalog(items,category='',full=False,brand=''):
  tabs='<a class="tab '+('active' if not category else '')+'" href="/catalog/" data-filter="">Все запчасти</a>'+''.join(f'<a href="/category/{k}/" class="tab {"active" if k==category else ""}" data-filter="{k}">{v[0]}</a>' for k,v in CATS.items())
  options=''.join(f'<option value="{e(v)}" {"selected" if v==brand else ""}>{e(v)}</option>' for v in BRANDS.values())
  more=f'<button class="btn outline" id="show-more">Показать ещё {icon("down")}</button>' if full else f'<a class="btn outline" href="/catalog/">Посмотреть весь каталог {icon("arrow")}</a>'
  return f'''<div class="catalog" data-limit="{12 if full else 8}" data-default-category="{category}"><div class="tabs" aria-label="Категории запчастей">{tabs}</div><div class="filters"><label class="field-search">{icon('search')}<span class="sr-only">Артикул или название</span><input class="ym-disable-keys" id="catalog-search" type="search" placeholder="Артикул или название" autocomplete="off"></label><label><span class="sr-only">Бренд</span><select id="brand-filter"><option value="">Все бренды</option>{options}</select></label><label><span class="sr-only">Сортировка</span><select id="sort-filter"><option value="default">По умолчанию</option><option value="price-asc">Сначала дешевле</option><option value="price-desc">Сначала дороже</option><option value="name">По артикулу</option></select></label></div><div class="grid" id="product-grid">{''.join(card(p) for p in items)}</div><div class="empty-state" hidden><h3>Ничего не найдено</h3><p>Проверьте номер или опишите нужную деталь в запросе.</p><button class="btn outline" data-reset style="margin-top:20px">Сбросить фильтры</button></div><div class="catalog-bottom">{more}<p><span id="result-count" aria-live="polite">{len(items)} позиций</span> · Цены указаны в рублях. Наличие и доставку уточним перед заказом.</p></div></div>'''
 def article_card(a):return f'''<article class="article-card"><div class="article-meta"><span>{a['category']}</span><span>{a['time']}</span></div><h3><a href="/articles/{a['slug']}/">{a['title']}</a></h3><p>{a['lead']}</p><a class="text-link" href="/articles/{a['slug']}/">Читать статью {icon('arrow')}</a></article>'''
 def contact():return f'''<section class="contact" id="selection"><div class="wrap contact-layout"><div><h2>Помочь с<br><span>подбором?</span></h2><p>Напишите артикул или опишите, какая деталь нужна.</p><small>Укажите модель техники и двигателя, если знаете.</small></div>{form('inquiry')}</div></section>'''
 featured=sorted(P,key=lambda p:(not bool(p.get('image')),p['sourceRow']))
 hero=f'''<section class="hero"><div class="wrap hero-inner"><div class="hero-copy"><h1>Топливная аппаратура для дизельной спецтехники</h1><p>Форсунки, ТНВД, распылители и клапаны Bosch, Delphi, Denso, John Deere и VDO. Найдите деталь по артикулу или напишите нам для подбора.</p><form class="searchbox" action="/catalog/" id="hero-search"><label class="sr-only" for="hero-query">Поиск по артикулу</label><input class="ym-disable-keys" id="hero-query" name="q" type="search" placeholder="Введите артикул или название" autocomplete="off"><button aria-label="Найти запчасть" type="submit">{icon('arrow')}</button></form><div class="example">Например: 0445120075 или RE539764</div><a class="btn" href="#catalog">Перейти в каталог {icon('down')}</a></div><div class="hero-visual"><img src="/assets/hero.webp" alt="Иллюстрация компонентов дизельной топливной системы" width="1536" height="1024" fetchpriority="high"></div></div></section><div class="brands"><div class="wrap brand-row"><span><a class="brand-logo" href="/brands/bosch/"><img src="/assets/brand-bosch.webp" alt="Bosch" width="433" height="97"></a></span><span><a class="brand-logo" href="/brands/delphi/"><img src="/assets/brand-delphi.webp" alt="Delphi" width="573" height="180"></a></span><span><a class="brand-logo" href="/brands/denso/"><img src="/assets/brand-denso.webp" alt="DENSO" width="140" height="53"></a></span><span class="deere"><a class="brand-logo" href="/brands/john-deere/"><img src="/assets/brand-john-deere.webp" alt="John Deere" width="192" height="36"></a></span><span><a class="brand-logo" href="/brands/vdo/"><img src="/assets/brand-vdo.webp" alt="VDO" width="250" height="50"></a></span></div></div>'''
 faq=[('Как проверить, подойдёт ли деталь?','Сверьте полный артикул. Если остались сомнения, пришлите модель техники и двигателя, а также серийный номер.'),('Можно заказать несколько деталей?','Добавьте их в корзину, укажите количество и отправьте запрос. Итоговую цену и условия доставки подтвердим перед заказом.'),('Куда доставляете?','Отправляем заказы по России. Стоимость и срок зависят от города и выбранной транспортной компании.'),('Что делать, если артикула нет?','Опишите нужный узел и укажите модель техники. Если маркировка сохранилась, приложите её фотографию.'),('Цена и наличие актуальны?','Перед оформлением подтвердим цену, наличие и комплектность.')]
 priority_products=[p for sku in ('0445020089','0445020110','DZ10599','0445020540','0445120072') for p in P if p['sku']==sku]
 priority_labels={}
 for p in priority_products:
  if p['sku']=='DZ10599':priority_labels[p['sku']]='Комплект John Deere DZ10599'
  elif p['category']=='pumps':priority_labels[p['sku']]=f'ТНВД {p["brand"]} {p["sku"]}'
  elif p['category']=='injectors':priority_labels[p['sku']]=f'Форсунка {p["brand"]} {p["sku"]}'
  else:priority_labels[p['sku']]=f'{p["shortName"]} {p["brand"]} {p["sku"]}'
 priority_links=''.join(f'<li><a class="text-link" href="/catalog/{p["id"]}/">{e(priority_labels[p["sku"]])}</a></li>' for p in priority_products)
 category_links=''.join(f'<li><a class="text-link" href="/category/{key}/">{label}</a></li>' for key,label in [('injectors','Дизельные форсунки'),('pumps','ТНВД'),('nozzles','Распылители'),('valves','Клапаны')])
 home=hero+f'''<section class="section wrap" id="catalog"><div class="section-heading"><h2>Каталог запчастей</h2><p>58 позиций · 5 брендов</p></div>{catalog(featured[:8])}<div class="selection-note">{icon('document')}<h3>Начните с номера детали</h3><p>Сверьте маркировку с артикулом в каталоге. Если нужна помощь, укажите модель техники и двигателя.</p><a href="#selection" class="text-link">Запросить подбор {icon('arrow')}</a></div><div class="selection-note"><h3>Ищите по артикулу</h3><div><ul>{priority_links}</ul><p>Или выберите раздел:</p><ul>{category_links}</ul></div></div></section><section class="about-band" id="about"><div class="wrap about-layout"><h2>Запчасти для дизельной техники</h2><div><p>СМ ТЕХНО поставляет запчасти для дизельной техники по России. В каталоге есть форсунки Common Rail, ТНВД, распылители, клапаны и компоненты двигателя.</p><p>В карточках указаны артикулы, цены и технические данные. Для проверки применимости пришлите маркировку детали и данные двигателя.</p><a class="text-link" href="/catalog/">Весь каталог {icon('arrow')}</a></div></div></section><section class="section wrap" id="how-to-order"><h2>Как сделать заказ</h2><div class="steps"><div class="step"><div class="step-number">01</div><h3>Выберите детали</h3><p>Найдите позиции по артикулу и укажите количество.</p></div><div class="step"><div class="step-number">02</div><h3>Проверьте применимость</h3><p>Пришлите модель техники, двигателя и серийный номер.</p></div><div class="step"><div class="step-number">03</div><h3>Подтвердите заказ</h3><p>До оплаты согласуем цену, комплектность и доставку.</p></div></div></section>'''+contact()+f'''<section class="section wrap"><div class="section-heading"><h2>Полезно знать</h2><a class="text-link" href="/articles/">Все статьи {icon('arrow')}</a></div><div class="article-grid">{''.join(article_card(a) for a in ARTICLES[:3])}</div></section><section class="section wrap faq"><div class="faq-layout"><h2>Частые вопросы</h2><div>{''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in faq)}</div></div></section>'''
 company=seo.commerce['company'];company['legal_name']=company.get('legal_name') or 'ООО «СМ ТЕХНО»'
 company_rows=''.join(f'<div><dt>{label}</dt><dd>{e(company[key])}</dd></div>' for key,label in [('legal_name','Юридическое наименование'),('postal_address','Юридический адрес'),('inn','ИНН'),('kpp','КПП'),('ogrn','ОГРН')] if company.get(key))
 company_contacts=''
 phones=([company['phone']] if company.get('phone') else [])+company.get('additional_phones',[])
 emails=([company['email']] if company.get('email') else [])+company.get('additional_emails',[])
 if phones:company_contacts+='<p>Телефоны: '+' · '.join(f'<a href="tel:{re.sub(r"[^+0-9]","",phone)}">{e(phone)}</a>' for phone in phones)+'</p>'
 if emails:company_contacts+='<p>Электронная почта: '+' · '.join(f'<a href="mailto:{e(email)}">{e(email)}</a>' for email in emails)+'</p>'
 if company.get('city'):company_contacts+=f'<p>Город: {e(company["city"])}</p>'
 if company.get('hours'):company_contacts+=f'<p>Режим работы: {e(company["hours"])}</p>'
 home+=f'<section class="section wrap company-summary"><h2>О компании</h2><p>Подбираем детали для дизельной техники по артикулу и данным двигателя. <a href="/about/">Как мы работаем</a>.</p><div class="company-contacts">{company_contacts}</div><a href="/contacts/" class="text-link">Контакты {icon("arrow")}</a></section>'
 page('/','Дизельные форсунки и ТНВД - топливная аппаратура | СМ ТЕХНО','Каталог топливной аппаратуры Bosch (Бош), Delphi (Делфи), Denso (Денсо), John Deere: дизельные форсунки, ТНВД, распылители и клапаны. Подбор по артикулу, цены и доставка по России.',home,{'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in faq]})
 page('/catalog/','Каталог топливной аппаратуры: цены и артикулы - СМ ТЕХНО','58 позиций Bosch, Delphi, Denso, John Deere и VDO: топливные форсунки, ТНВД, клапаны и распылители. Подбор запчастей с поставкой по России.',crumbs([('Каталог',None)])+'<div class="wrap page-title"><h1>Каталог запчастей</h1><p>Топливная аппаратура и компоненты двигателя. Найдите деталь по артикулу, выберите бренд или нужный узел.</p></div><section class="wrap section catalog-page">'+catalog(featured,full=True)+'</section>'+contact())
 for key,(label,title,description) in CATS.items():
  items=[p for p in featured if p['category']==key]
  page('/category/'+key+'/',title+' - цены и подбор | СМ ТЕХНО',description,crumbs([('Каталог','/catalog/'),(label,None)])+f'<div class="wrap page-title"><h1>{title}</h1><p>{description}</p></div><section class="wrap section catalog-page">'+catalog(items,category=key,full=True)+'</section>'+contact())
 for key,brand in BRANDS.items():
  items=[p for p in featured if p['brand']==brand]
  description=f'Запчасти {brand} для дизельной техники. Выберите товар по артикулу и сверьте данные двигателя перед заказом.'
  page('/brands/'+key+'/',f'Запчасти {brand} - каталог и цены | СМ ТЕХНО',description,crumbs([('Каталог','/catalog/'),(brand,None)])+f'<div class="wrap page-title"><h1>Запчасти {brand}</h1><p>{description}</p></div><section class="wrap section catalog-page">'+catalog(items,full=True,brand=brand)+'</section>'+contact())
 ARTICLE_BY_SLUG={a['slug']:a for a in ARTICLES}
 ARTICLE_MAP={k:[a for a in ARTICLES if a['related']==k][:2] for k in CATS}
 for p in P:
  path='/catalog/'+p['id']+'/'
  title=f"{p['shortName']} {p['brand']} {p['sku']} - цена | СМ ТЕХНО"
  desc=product_description(p)
  schema=seo.product_schema(p)
  credit='Изображение может быть иллюстрацией. Комплектность уточните перед заказом.'
  codes=''.join(f'<span>{e(c)}</span>' for c in p['codes'])
  related=sorted([x for x in featured if x['category']==p['category'] and x['id']!=p['id']],key=lambda x:(x['brand']!=p['brand'],not bool(x.get('image')),x['sourceRow']))[:4]
  articles=ARTICLE_MAP[p['category']] or [a for a in ARTICLES if a['slug']=='spisok-zapchastey-dlya-zakaza']
  if not any(a['slug']=='spisok-zapchastey-dlya-zakaza' for a in articles):articles=articles+[ARTICLE_BY_SLUG['spisok-zapchastey-dlya-zakaza']]
  state=seo.availability(p)
  stock=f'<link itemprop="availability" href="https://schema.org/{state}">'+stock_label(p) if state else ''
  if state and p.get('stockQuantity') is not None:stock+=f'<span itemprop="inventoryLevel" itemscope itemtype="https://schema.org/QuantitativeValue"><meta itemprop="value" content="{p["stockQuantity"]}"><meta itemprop="unitCode" content="H87"></span>'
  p_name=seo.product_name(p)
  technical=technical_section(p)
  content=crumbs([('Каталог','/catalog/'),(CATS[p['category']][0],'/category/'+p['category']+'/'),(p['sku'],None)])+f'''<div class="wrap"><article itemscope itemtype="https://schema.org/Product" itemid="{e(base+path)}#product"><section class="product-detail"><div><div class="detail-photo">{picture(p,True)}</div><div class="photo-credit">{e(credit)}</div></div><div><div class="brand-label" itemprop="brand">{e(p['brand'])}</div><h1 itemprop="name">{e(p_name)}</h1><div class="detail-sku">Артикул: <strong itemprop="sku">{e(p['sku'])}</strong></div><div itemprop="offers" itemscope itemtype="https://schema.org/Offer" itemid="{e(base+path)}#offer"><meta itemprop="price" content="{p['price']}"><meta itemprop="priceCurrency" content="RUB"><link itemprop="url" href="{e(base+path)}"><div class="detail-price">{money(p['price'])} ₽</div>{stock}<p class="price-note">Наличие и комплектность подтвердим перед заказом.</p></div><button class="btn" data-add="{e(p['id'])}">{icon('plus')} В корзину</button><dl class="specs"><div><dt>Бренд</dt><dd><a href="/brands/{next(k for k,v in BRANDS.items() if v==p['brand'])}/">{e(p['brand'])}</a></dd></div><div><dt>Артикул</dt><dd>{e(p['sku'])}</dd></div><div><dt>Раздел</dt><dd><a href="/category/{e(p['category'])}/">{e(CATS[p['category']][0])}</a></dd></div><div><dt>Регион продаж</dt><dd>Россия</dd></div></dl><nav class="product-anchor-nav" aria-label="Информация о товаре"><a href="#description">Описание</a><a href="#part-numbers">Артикулы</a>{'<a href="#technical">Характеристики</a>' if TECHNICAL.get(p['sku'],{}).get('facts') else ''}<a href="#order-details">Как заказать</a></nav></div></section><section class="product-description" id="description"><h2>О детали</h2><div itemprop="description"><p>{e(p['copy'][0])}</p> <p>{e(p['copy'][1])}</p></div></section><section class="product-description" id="part-numbers"><h2>Номера для сверки</h2><div><p>Сверьте артикул с маркировкой детали. Остальные номера из карточки помогут при поиске, но перед заказом проверьте их связь с нужным исполнением.</p><div class="code-list">{codes}</div></div></section>{technical}</article><section class="product-description" id="order-details"><h2>Как заказать</h2><div><p>Добавьте товар в корзину и укажите количество. Если нужна проверка применимости, сообщите модель техники и двигателя, серийный номер и номер установленного узла.</p><p>Перед заказом подтвердим цену, наличие, состояние и комплектность. Для расчёта доставки укажите город.</p><p><a class="text-link" href="/delivery/">Доставка и оплата {icon('arrow')}</a></p></div></section><section class="section product-reading"><div class="section-heading"><h2>Полезные статьи</h2></div><div class="article-grid">{''.join(article_card(a) for a in articles[:2])}</div></section><section class="section"><div class="section-heading"><h2>Другие детали в разделе</h2><a class="text-link" href="/category/{e(p['category'])}/">Весь раздел {icon('arrow')}</a></div><div class="grid">{''.join(card(x)for x in related)}</div></section></div>'''+contact()
  page(path,title,desc,content,schema)
 page('/articles/','Статьи о подборе дизельных запчастей | СМ ТЕХНО','Как сверить артикул, выбрать ТНВД и понять, какая деталь нужна для ремонта.',crumbs([('Статьи',None)])+'<div class="wrap page-title"><h1>Статьи о запчастях</h1><p>Короткие ответы о подборе и заказе деталей для дизельной техники.</p></div><section class="section wrap catalog-page"><div class="article-grid articles-list">'+''.join(article_card(a)for a in ARTICLES)+'</div></section>')
 for a in ARTICLES:
  article_schema={'@context':'https://schema.org','@type':'Article','headline':a['title'],'description':a['lead'],'inLanguage':'ru-RU','author':{'@type':'Organization','name':'СМ ТЕХНО'},'publisher':{'@type':'Organization','name':'СМ ТЕХНО'},'mainEntityOfPage':base+'/articles/'+a['slug']+'/'}
  content=crumbs([('Статьи','/articles/'),(a['title'],None)])+f'''<div class="article-hero"><div class="wrap"><div class="article-meta"><span>{a['category']}</span><span>{a['time']} чтения</span></div><h1>{a['title']}</h1><p class="lead">{a['lead']}</p></div></div><article class="wrap read-content">{''.join(f'<section><h2>{h}</h2><p>{p}</p></section>'for h,p in a['sections'])}<aside class="read-cta"><h3>Нужна деталь?</h3><p>Найдите её в каталоге или отправьте запрос на подбор.</p><a class="btn" href="/category/{a['related']}/">{CATS[a['related']][0]} {icon('arrow')}</a></aside></article>'''
  page('/articles/'+a['slug']+'/',a['title']+' - СМ ТЕХНО',a['lead'],content,article_schema)
 delivery=seo.commerce['company'].get('delivery_terms','')
 payment=seo.commerce['company'].get('payment_terms','')
 delivery_content='<div class="wrap page-title"><h1>Доставка и оплата</h1><p>Доставляем заказы по России.</p></div><div class="wrap read-content"><h2>Перед заказом</h2><p>Пришлите список артикулов, количество и город доставки. Менеджер подтвердит цену и наличие до выставления счёта. Срок поставки и доставки сообщим до оплаты.</p><h2>Оплата</h2><p>'+ (e(payment) if payment else 'Условия оплаты сообщим до оформления заказа. Онлайн-оплата на сайте не предусмотрена.') + '</p><h2>Доставка и самовывоз</h2><p>'+ (e(delivery) if delivery else 'Стоимость и срок доставки зависят от адреса и выбранной транспортной компании.') + '</p><h2>Получение заказа</h2><p>При получении сверьте маркировку и количество, проверьте упаковку. Если покупаете комплект, уточните его состав до оплаты.</p><p><a href="/#selection" class="btn">Отправить запрос</a> <a href="/catalog/" class="btn outline">Подобрать запчасть</a></p></div>'
 page('/delivery/','Доставка и оплата запчастей | СМ ТЕХНО','Оплата по счёту, доставка по России транспортной компанией или самовывоз.',crumbs([('Доставка и оплата',None)])+delivery_content)
 company=seo.commerce['company']
 company_rows=''.join(f'<div><dt>{label}</dt><dd>{e(company[key])}</dd></div>' for key,label in [('legal_name','Юридическое наименование'),('postal_address','Юридический адрес'),('inn','ИНН'),('kpp','КПП'),('ogrn','ОГРН')] if company.get(key))
 company_contacts=''
 if company.get('phone'):
  phone=company['phone'];href=re.sub(r'[^+0-9]','',phone);company_contacts+=f'<p>Телефон: <a href="tel:{href}">{e(phone)}</a></p>'
 if company.get('email'):
  email=company['email'];company_contacts+=f'<p>Email: <a href="mailto:{e(email)}">{e(email)}</a></p>'
 for phone in company.get('additional_phones',[]):company_contacts+=f'<p>Телефон: <a href="tel:{re.sub(r"[^+0-9]","",phone)}">{e(phone)}</a></p>'
 for email in company.get('additional_emails',[]):company_contacts+=f'<p>Email: <a href="mailto:{e(email)}">{e(email)}</a></p>'
 if company.get('city'):company_contacts+=f'<p>Город: {e(company["city"])}</p>'
 if company.get('hours'):company_contacts+=f'<p>Режим работы: {e(company["hours"])}</p>'
 page('/about/','О компании СМ ТЕХНО - запчасти для дизельной техники','Подбираем детали по артикулу и данным двигателя, поставляем по России.',crumbs([('О компании',None)])+'<div class="wrap page-title"><h1>О компании СМ ТЕХНО</h1><p>Запчасти для дизельных двигателей и топливных систем.</p></div><div class="wrap read-content"><h2>Что мы поставляем</h2><p>В каталоге есть форсунки, ТНВД, распылители, клапаны, топливные насосы и ремонтные комплекты Bosch, Delphi, Denso, John Deere и VDO.</p><h2>Как подобрать деталь</h2><p>Начните с полного артикула. Если нужна проверка, пришлите модель техники, данные двигателя и серийный номер. Номера для сверки помогают найти позицию, но применимость и состав комплекта важно подтвердить перед заказом.</p><h2>Заказ и доставка</h2><p>Работаем с заказами по России. До оплаты подтвердим цену, наличие, состояние и комплектность товара, а также стоимость и срок доставки. На сайте можно собрать список деталей и отправить запрос.</p><p><a class="text-link" href="/catalog/">Каталог</a> · <a class="text-link" href="/#selection">Запросить подбор</a> · <a class="text-link" href="/delivery/">Доставка и оплата</a> · <a class="text-link" href="/contacts/">Контакты</a></p></div>')
 page('/contacts/','Контакты СМ ТЕХНО - подбор запчастей','Телефоны и почта СМ ТЕХНО. Для подбора укажите артикул и данные техники.',crumbs([('Контакты',None)])+'<div class="wrap page-title"><h1>Контакты</h1><p>Позвоните или напишите нам по вопросам подбора и заказа.</p></div><div class="wrap read-content">'+company_contacts+('<h2>Реквизиты компании</h2><dl class="specs">'+company_rows+'</dl>' if company_rows else '')+'<h2>Для подбора</h2><p>Укажите артикул и количество. Если номер неизвестен, опишите деталь и пришлите модель техники, двигателя и серийный номер.</p><p>Для расчёта доставки напишите город получения.</p></div>'+contact())
 page('/privacy/','Политика обработки персональных данных - СМ ТЕХНО','Как СМ ТЕХНО обрабатывает данные запросов на заказ и поставку запчастей.',crumbs([('Обработка данных',None)])+'<div class="wrap page-title"><h1>Политика обработки персональных данных</h1></div>'+document('PRIVACY.md'))
 page('/consent/','Согласие на обработку персональных данных - СМ ТЕХНО','Отдельное согласие на обработку запроса о заказе и поставке запчастей.',crumbs([('Согласие на обработку данных',None)])+'<div class="wrap page-title"><h1>Согласие на обработку персональных данных</h1></div>'+document('CONSENT.md'))
 page('/404/','Страница не найдена - СМ ТЕХНО','Найдите запчасть в каталоге СМ ТЕХНО.', crumbs([('Страница не найдена',None)])+'<div class="section wrap"><h1>Страница не найдена</h1><p style="margin:25px 0">Проверьте адрес или перейдите в каталог.</p><a class="btn" href="/catalog/">Открыть каталог</a></div>')
 paths.remove('/404/')
 seo.finish(paths)
 (stage/'data/catalog-built.json').write_text(json.dumps(P,ensure_ascii=False,indent=2),encoding='utf-8')
 (stage/'data/seo-catalog.json').write_text(json.dumps([{'sku':p['sku'],'path':'/catalog/'+p['id']+'/','title':p['shortName']+' '+p['brand']+' '+p['sku']+' - цена | СМ ТЕХНО','description':product_description(p),'h1':seo.product_name(p),'image_alt':seo.product_name(p) if p.get('image') else None,'paragraphs':p['copy'][:2],'stockQuantity':p['stockQuantity'],'availability':seo.availability(p)} for p in P],ensure_ascii=False,indent=2),encoding='utf-8')
 (stage/'backend').mkdir()
 (stage/'backend/catalog.json').write_text(json.dumps([{k:p[k] for k in ['id','sku','name','brand','price']} for p in P],ensure_ascii=False,indent=2),encoding='utf-8')
 # A single dependency-free Worker includes pre-rendered pages and locally hosted assets.
 (OUT/'.openai').mkdir();shutil.copy(ROOT/'.openai/hosting.json',OUT/'.openai/hosting.json')
 assets={}
 for f in OUT.rglob('*'):
  if f.is_file():
   if '.openai' in f.relative_to(OUT).parts:continue
   key='/'+f.relative_to(OUT).as_posix();mime=mimetypes.guess_type(f.name)[0] or 'application/octet-stream';binary=f.suffix.lower() not in ['.html','.css','.js','.json','.xml','.txt','.svg'];assets[key]={'type':mime,'binary':binary,'body':base64.b64encode(f.read_bytes()).decode() if binary else f.read_text(encoding='utf-8')}
 orders=(ROOT/'src/orders.mjs').read_text(encoding='utf-8').replace('export async function handleOrder','async function handleOrder')
 runtime=(ROOT/'src/worker-runtime.mjs').read_text(encoding='utf-8')
 worker='const ASSETS='+js(assets)+';\nconst PRODUCTS='+js(P)+';\nconst INDEXABLE='+str(indexable).lower()+';\n'+orders+'\n'+runtime
 (OUT/'server').mkdir(exist_ok=True);(OUT/'server/index.js').write_text(worker,encoding='utf-8')
 publish_files({OUT:ROOT/'dist',stage/'data/catalog-built.json':ROOT/'data/catalog-built.json',stage/'data/seo-catalog.json':ROOT/'data/seo-catalog.json',seo.state_root/'seo-state.json':ROOT/'data/seo-state.json',seo.state_root/'seo-changes.json':ROOT/'data/seo-changes.json',stage/'backend/catalog.json':ROOT/'backend/catalog.json'},journal_root=ROOT)
 print(json.dumps({'pages':len(paths)+1,'products':len(P),'photos':sum(bool(p.get('image'))for p in P),'articles':len(ARTICLES),'indexable':indexable,'workerKB':round(len(worker.encode())/1024)},ensure_ascii=False))
