# Выпуск 1 ноября 2026: топливо перед морозами

## Сценарий и affected checkset

Известный ограниченный выпуск: новая оригинальная статья, WebP и запись ARTICLES; рекомендации через неизменённый механизм, списки, sitemap и семантическая карта. Без изменений архитектуры, шаблонов, backend/API, цен, остатков, характеристик, утверждённых VAT и подтверждений форм. База свежего origin/main 0b4605aa3fa2f27633799fcc6e6c8b512a73d1f3, временная ветка codex/article-winter-fuel-20261101 в сохранённом чистом изолированном worktree. Сценарий для закупщика и механика: установить фактическую партию и остатки топлива до морозов, согласовать подготовку, не заказывать ТНВД по одному симптому.

Единая существующая fail-fast команда проверок в PowerShell с PYTHONUTF8=1, PYTHONIOENCODING=utf-8, PUBLIC_SITE_URL=https://engine.cmteh.ru и INDEXABLE=true: python build.py; python tools/build_semantic_core.py; python tests/article-publication.test.py; python tests/seo.test.py; python tests/catalog.test.py; python tools/build_semantic_core.py --check; git diff --check. Отдельно узко проверить фактическую новую страницу, источники, WebP, метаданные, прямые/обратные ссылки, списки и sitemap; desktop1440/mobile390. Пакет из проверенного источника, строгий helper с актуальными pins и резервными копиями, реальные POSIX fixtures, одно свежее независимое ревью release gate. Не создавать новые тестовые wrapper-команды или GitHub Actions.

## Выбор темы и границы дублей

Проверены 13 существующих статей и последние журналы. Кандидаты: чтение протокола стенда (вчерашний выпуск, исключён); запуск после фильтра (29 октября, исключён); фактическая сезонность оставшегося топлива перед морозами (выбрано). От пилота холодного запуска отличается фокусом на подготовке партий и остатках в складской ёмкости, а не стартере/подогреве/диагностике форсунок. От статьи о воде отличается причиной ограничения подачи и разговором о сезонности; сигнал воды заново не разбирается. Не создаёт вторую инструкцию замены фильтра или подбор присадки/ремонтную услугу магазина.

Свежий сигнал вопроса: https://www.reddit.com/r/kubota/comments/1x4e38d/how_long_until_winter_diesel_shows_up/ . Выдача при проверке 01.11.2026 показывает вопрос о появлении зимнего топлива от 12.10.2026. Прямое открытие вернуло Cache miss: используем только видимый вопрос из выдачи, не утверждаем, что прочитали полную ветку. Канадский контекст не подтверждает сроки перехода на топливо в России. Это один вопрос, не массовая тенденция. Советы комментариев о смесях и способах отогрева в статью не переносим.

Сезонность - редакционное основание на начало ноября, не заявление о текущей погоде конкретного региона. Новая тема не имеет измеренной частотности. Исторические данные семантического ядра не переносим в текущий спрос и не добавляем услугу диагностики в каталог.

## Первичные источники, проверено 01.11.2026

- https://www.perkins.com/en_GB/aftermarket/maintenance/maintenance-advice/Winter-diesel-dos-and-donts.index.html : разделы Fuel и Filters рекомендуют winter blended fuel, внимание фильтру, предварительное обслуживание и запасной элемент. Берём только эти пункты; не переносим отдельные числа запуска, батареи, состав DEF, сроки прогрева и иные неприменимые универсальные нормы.
- https://www.donaldson.com/en/resources/technical-articles/cold-weather-diesel-engine-maintenance-tips/ : при охлаждении парафиновые твёрдые частицы могут ограничить фильтр; поставщику задают вопросы о предстоящих условиях; нельзя снижать эффективность фильтрации; присадки по инструкции, не в холодное топливо. Никаких американских #1/#2 рецептов смешивания, дозировок, процентов биодизеля, универсальных CFPP-границ или характеристик наших ТНВД. Подозрительные числовые конверсии источника в материал не включены.

Редакционные рекомендации: сохранять документы фактической партии, историю доливов/остатков и условия предстоящей работы; неизвестное честно обозначать. Рекомендации не являются нормативным бланком, правилом допуска или обещанием, что конкретная партия топлива выдержит температуру. Нет объявления любого помутнения диагнозом, замены насоса по симптому, инструкции самостоятельного вскрытия Common Rail/огня/слива/перелива. Не назначаем составы присадок, сроки смены по календарю, топливо/технику для конкретного региона. Технические утверждения ограничены двумя первичными источниками, текст оригинальный.

## Каталог и ссылки

Фактические публичные H1 и source catalog проверены: /catalog/9323a270g/ - ТНВД Delphi 9323A270G; /catalog/0445020610/ - ТНВД Bosch 0445020610. Оба category pumps. Это разные позиции, применимость к Perkins/Kubota или другим двигателям не заявлена. Обратные ссылки по существующему related=pumps и products. Раздел /category/pumps/, связанные /articles/tnvd-pered-zakazom/ и /articles/posle-zameny-toplivnogo-filtra-dizel-ne-zavoditsya/ проверены по тексту. Новый /articles/letnee-toplivo-pered-morozami/ до работы отдаёт реальный404.

## Иллюстрация

Условный металлический ТНВД и отдельно закрытая канистра на светлом бетоне, мягкий свет, графит и жёлтый акцент, лёгкий холодный оттенок фона. Не фотография конкретного артикула/комплекта, не схема работы или способ подготовки топлива. Built-in ImageGen; без надписей и логотипов, анимации и Anatomy. PNG вне public, WebP с явными width/height и содержательным alt. Сохраняется принятое поведение без технической подписи под обложкой. Финальный WebP 169328 байт, RGB 1400×933.

## Промпт встроенного ImageGen

Use case: product-mockup
Asset type: editorial website article cover, landscape 3:2
Primary request: a photorealistic, restrained industrial still life for an article about checking summer diesel fuel before cold weather. This is a generic conceptual illustration, not a photograph of any specific part number.
Scene/backdrop: pale neutral studio background with an extremely subtle cool grey-blue cast suggesting late autumn; two low light-grey concrete plinths on a matching surface.
Subject: one realistic generic metal high-pressure diesel injection pump, intact and standalone, on the left plinth. On the right a small closed graphite-grey metal fuel canister with a simple yellow screw cap and modest integrated handle. Keep a visible gap between the pump and the closed canister; no connections between them.
Style/medium: premium photorealistic product photography, brushed and cast metal detail, honest physical proportions, concrete pores, soft natural shadows. Match the restrained light concrete, metal and graphite visual language of the site's covers.
Composition/framing: balanced three-quarter eye-level view, pump as main foreground subject and the canister a little behind it; generous clean margins, both objects fully inside the landscape frame.
Lighting/mood: soft diffuse studio daylight, calm technical editorial mood.
Color palette: silver metal, graphite, pale grey concrete, one small yellow accent on the canister cap.
Text: none.
Constraints: no text, no digits, no labels, no logos, no invented trademarks, no barcode or QR code. No frost, ice or snow on the parts. No open container, no liquid visible, no fuel transfer, no hoses, no disassembly, no flame, no smoke, no people, no tools, no diagnostics or claims of an actual product set.
