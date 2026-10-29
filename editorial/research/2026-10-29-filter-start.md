# Выпуск 29 октября: запуск после замены топливного фильтра

Сценарий: после обслуживания двигатель запускается хуже; владелец собирает историю работ, а закупщик ждёт подтверждённого перечня деталей. Известное ограниченное изменение: статья, запись реестра, новый WebP и штатные индексы SEO. Один исполнитель готовит текст напрямую по политике 27 октября; независимая подготовка безопасного выпуска и обложки делегирована, одно свежее ревью охватит итоговый материал и связанные с релизом guard-артефакты. BASE 0b9e8e0300755f4c79cb4817b7508abb4a1160b5, ветка codex/article-filter-start-20261029 в сохранённом чистом изолированном worktree.

Рассмотрены три направления: повторное загрязнение фильтра (пересекается с опубликованной темой воды в топливе), повторная негерметичность после замены форсунки (вчерашний выпуск, исключён), ухудшение запуска после замены фильтра. Выбрана последняя тема: конкретный момент появления проблемы и порядок передачи сведений перед заказом насоса отличают её от общего материала о холодном запуске и списка проверок ТНВД. Измеренная новая частотность и массовая тенденция не заявляются. Сверены реестр и подготовленные исследования проекта; новый URL до работы возвращает 404.

## Сигналы аудитории и границы переноса

Проверено 29 октября: [Ram, prolonged cranking after fuel filter change](https://www.reddit.com/r/ram_trucks/comments/1x5why3/2026_ram_3500_cranking_for_longer_after_fuel/) содержит жалобу на более долгий запуск после замены. Поисковая выдача указывает 14 октября 2026, открытая версия показывает относительную дату, не согласующуюся с ней; точную дату публикации не считаем подтверждённой. Текст вопроса открыт и прочитан. Это один сигнал вопроса, не данные о распространённости и не основание считать проблему типовой для спецтехники. Советы о циклах зажигания, прошивках, затяжке и открытии соединений не перенесены.

Второй открытый сигнал: [Kubota BX23, suspected tank contamination](https://www.reddit.com/r/kubota/comments/1xfdygd/bx23_kubota_tractor_suspected_fuel_tank/), в поиске 25 октября 2026, о загрязнении недавно чистого фильтра. Это основание рассмотреть соседнюю тему, но она отклонена из-за пересечения с уже опубликованной статьёй; цвет загрязнения, биоциды, самодельные фильтры и ремонтные советы из ответов не используются.

## Первичные источники и вывод

Обе страницы Delphi полностью открыты 29 октября, ссылки сохранены в тексте статьи. Common Rail filter guidance описывает ограничения подачи, подсос воздуха и утечки; пример 2.0 HDi разделяет проверку подачи к ТНВД и оценку высокого давления. Пределы, числа и процедуры этих автомобильных примеров не перенесены на спецтехнику. Пересказ каждого источника короче 200 слов. Не утверждается, что замена фильтра доказала попадание воздуха или неисправность насоса. Чек-лист истории работ, сохранение отчёта и требования к заключению являются редакционным практическим выводом. Самостоятельных измерений, разборки Common Rail, поиска течи рукой и универсальной прокачки нет.

Карточки 9323a270g и 9323a260g проверены 29 октября по HTTP 200 и фактическим H1 с полными артикулами Delphi. Ссылки ведут на реальные насосы, раздел pumps и две существующие статьи; обратные рекомендации формирует существующий механизм. Применимость, взаимозаменяемость, наличие фильтра в поставке и характеристики не выдуманы. Не меняются цены, остатки, товарные сведения, backend/API, JavaScript, конфигурация, cron или принятый шаблон без технической подписи под картинкой.

Затронутый существующий checkset: production build, tools/build_semantic_core.py, tests/article-publication.test.py, tests/seo.test.py, tests/catalog.test.py, semantic-core --check и git diff --check. Fail-fast команда документирована в выпуске 26 октября. Дополнительно проверить фактический новый URL/метаданные/ссылки/обратные рекомендации/WebP, desktop 1440 и mobile 390. Никаких новых wrapper-команд или дублирующих per-article тестовых блоков. Существующая проверка старой статьи о воде корректируется только для её выхода за пределы трёх последних статей на главной.

Релиз использует подтверждённый текущий baseline 28 октября, 199 файлов; защищённые production-байты сохраняются, YML отличается от пересборки только датой и остаётся прежним. Токен Яндекса вне пакета проверяется отдельно по external_preserved_paths до и после записи. Существующие guards, backup и rollback сохраняются; только привязка следующего пакета и baseline обновляется с доказательством обратимой замены метаданных.

## Обложка и промпт

Встроенный ImageGen; статичный WebP 1400x933, 121072 байта. Образец и результат после сжатия просмотрены; исходный PNG хранится вне публичного пакета. Условный характер отмечен в alt, редакционной записи и тексте о комплектности.

Use case: editorial-cover
Asset type: static 3:2 cover image for an article about poor diesel starting after fuel-filter replacement; check fuel supply before buying a high-pressure pump.
Input image: Image 1 is a style/composition reference only; match its spacious industrial product photography, neutral studio setting, and pale concrete display blocks.
Scene/backdrop: Light neutral grey studio background and pale concrete pedestals.
Subject: Foreground left, a clean generic complete cylindrical diesel fuel-filter assembly with graphite housing, metallic top, and small yellow protective cap. Background right, separate generic graphite and silver high-pressure fuel pump on a slightly higher concrete block. Both parts entirely visible and not connected.
Style/medium: Photorealistic studio still life, realistic machined metal.
Composition/framing: Balanced spacious landscape 3:2 composition, objects distinct and fully in frame.
Lighting/mood: Soft studio lighting, natural soft shadows.
Constraints: No markings, text, logos, watermarks, labels, open pipes, fuel, hands, engine repair, or evidence of defect. Not an exact SKU photograph, kit, or interchangeability diagram. No animation.

Built-in image_gen mode; generated once successfully. Selected source PNG: C:\Users\Alexandr\.codex\generated_images\01a1863d-25ee-7df0-be87-ae143cc39079\exec-dced4ff8-9e02-488c-8958-6247b95db333.png
Reference: D:\codex\!engine.cmteh.ru\public\assets\hero.webp (style/composition reference only).
