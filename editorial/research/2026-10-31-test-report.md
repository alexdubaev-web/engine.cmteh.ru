# Выпуск 31 октября 2026: протокол проверки форсунки

## Сценарий и проверки

Ограниченный редакционный выпуск без изменения архитектуры, шаблонов, каталожных характеристик, цен или наличия. База origin/main 329c057910a211e579ff324394198c4f20b7f631. Новая временная ветка codex/article-test-report-20261031 в сохранённом чистом изолированном worktree. Добавить оригинальную статью, статичную обложку WebP и запись ARTICLES. Существующий механизм выдаёт две рекомендации на карточке: актуализировать только устаревшее ожидание старой статьи при вытеснении из этих двух мест. Принятые VAT, формы и поведение без технических подписей под обложками сохраняются.

Единый существующий affected checkset (PowerShell, PYTHONUTF8=1, PYTHONIOENCODING=utf-8, PUBLIC_SITE_URL=https://engine.cmteh.ru, INDEXABLE=true; прекращать при ненулевом коде): python build.py; python tools/build_semantic_core.py; python tests/article-publication.test.py; python tests/seo.test.py; python tests/catalog.test.py; python tools/build_semantic_core.py --check; git diff --check. Узкие проверки фактического нового URL, WebP, canonical/date/schema, прямых и обратных ссылок, списков и sitemap; desktop 1440 и mobile 390. Строгая процедура существующего deployment с актуальными metadata pins, реальными POSIX guard fixtures и одним свежим независимым ревью. Никаких новых тестовых wrapper-команд или GitHub Actions.

## Выбор темы и защита от дублей

Проверены все 12 опубликованных материалов и предыдущие журналы. Рассмотрены: затруднённый запуск после фильтра (выпуск 29 октября, исключён), происхождение и подлинность детали (выпуск 30 октября, исключён), содержание результата диагностики для закупщика (выбрано). Новый фокус: связать протокол с проверенной форсункой и согласованным перечнем деталей. Материал не повторяет инструкцию кодирования, холодного запуска или выбора распылителя.

Поисковый сигнал: https://www.reddit.com/r/Yanmar/comments/1x09vl6/test_these_injectors_first/ . Выдача при проверке 31.10.2026 показывает публикацию 07.10.2026 с вопросом о проверке форсунок перед покупкой и проверке комплекта. Прямое открытие web-инструментом вернуло Cache miss, поэтому основание ограничено видимым фрагментом выдачи. Это один вопрос аудитории, не доказательство массовой тенденции и не технический источник. Механическую pop-проверку из вопроса не переносим на Common Rail.

В семантическом ядре kw-00248, "проверка форсунки bosch", evidence ws-2026-10-12-q003-r046, историческое broad_row 93 за 05.09.2026–04.10.2026; kw-00254, "проверка форсунок делфи", ws-2026-10-12-q016-r050, broad_row 94 за тот же период. Это наблюдавшиеся широкие строки, не сегодняшняя частотность новой темы; не суммируются. Их primary_target остаётся существующим разделом, не создаём обещание услуг диагностики. Новая тема не имеет измеренной частотности.

## Первичные источники и границы утверждений

Проверено 31.10.2026:

- https://www.delphiautoparts.com/en-gb/mom/need-to-know/article/fuel-analyzer-tech-tips : в конкретном примере разнесены чтение ошибок/проверка системы на машине, авторизованный стенд с электрическими проверками, ремонт и повторное полное испытание. Использовано как пример, не правило снимать или менять комплект. Числа, коды ошибок, давление, инструменты и опасные сервисные действия в статью не перенесены. Не заимствуем клиентскую историю как свою.
- https://www.boschaftermarket.com/afr/en/diagnostic/test-equipment/test-benches-and-tools/dci-700/ : числовые/графические результаты, печатный отчёт, актуализация спецификаций. Страница конкретного оборудования не доказывает универсальную применимость стенда ко всем брендам и всем нашим SKU. Характеристики стенда и нормативы форсунок не заявляем.
- Дополнительно просмотрена https://www.delphiautoparts.com/test-equipment/hartridge/cri-pro/all-makes-injector-brochure : различие All-Makes и Authorised режимов и итоговый отчёт. Не используем в тексте, не рекомендуем оборудование и не заявляем авторизованность какого-либо сервиса.

Вопросы к сервису о номере, режиме, единицах, завершённости и заключении являются редакционной памяткой закупщику, не цитатой стандарта или обязательным бланком. Никаких универсальных норм обратного слива, диагноза по одному симптому, рецепта разборки или заявления ремонтных услуг магазина. Текст написан самостоятельно; сторонние материалы о протоколах не служат техническими источниками и не копируются.

## Ссылки и изображение

Реальные карточки проверены по H1 на публичном сайте (HTTPS, 200), не только по статусу: /catalog/0445120075/ Bosch и /catalog/28540276/ Delphi. Раздел /category/injectors/; связанные материалы /articles/podbor-po-artikulu/ и /articles/forsunka-ili-raspylitel/. Новый /articles/protokol-proverki-forsunki/ до работы отдаёт настоящий 404. Обратные ссылки формирует неизменённый механизм рекомендаций по двум SKU и разделу injectors. Применимость к двигателям, взаимозаменяемость, состояние и документы поставки не выдуманы.

Статичная условная иллюстрация встроенным ImageGen, не фотография конкретного артикула, не стенд, не образец реального протокола. Форсунка и чистый лист на планшете, без текста/чисел/графиков и результата проверки. Источник PNG хранится вне публичного пакета; финальный WebP 1400×933 с размерами и содержательным alt. Финал 122938 байт, 1400×933, RGB. Оригинал и WebP осмотрены, артефактов не замечено.

## Промпт ImageGen

Use case: product-mockup.
Asset type: static editorial article cover for a Russian diesel-parts website, landscape 3:2.
Primary request: create one restrained photorealistic studio still life about a diesel injector inspection report. A single generic metallic Common Rail diesel injector rests diagonally on a light pale concrete plinth. Beside it, on the same pale service surface, is a charcoal graphite clipboard holding one completely blank white sheet, with a small yellow clip as the only color accent.
Scene/backdrop: seamless light neutral grey background and pale concrete plinth, softly lit, no workshop clutter.
Style/medium: premium realistic industrial product photography; fine brushed silver metal, graphite connector, believable concrete texture, soft studio shadows. Match the quiet light-grey, silver, graphite and tiny yellow-accent look of the existing site photographs.
Composition/framing: balanced landscape composition, injector and blank clipboard clearly visible, generous breathing room, no cropping of injector tip or clipboard.
Text: none. The sheet is truly blank.
Constraints: generic conceptual illustration, not an exact photograph of any particular SKU or a testing instrument. No logos, brands, numbers, text, letters, QR codes, barcodes, tables, charts, graphs, PASS marks, certificate seals, test results, measuring equipment, people, hands, animation, watermark. No fake report or diagnostic conclusion.
