# Границы и правила

## Правила проекта

Python static generator, local HTML/CSS/JS, PHP backend. Реальные данные компании — data/commerce.json. Нет зависимостей для установки. Пользовательский AGENTS.md не изменять. Товарный/статейный контент не трогать. Нельзя менять цены, остатки, SKU, URL, API, документы/версию согласия, сессии, включение аналитики, CSP или обязательные deploy guards. Чужие рабочие файлы не затрагивать. Все изменения только task worktree.

## Границы, решённые в спецификации

- build.py: общий FOOTER, вызов page('/') и existing delivery_content; реквизиты брать из seo.commerce['company'], экранировать e().
- seo.py SEO.render(): только текст analytics_ui, существующие data-атрибуты и поведение hidden сохранить.
- public/assets/style.css: только при необходимости переносы нового блока реквизитов.
- docs/PRIVACY.md: краткая ссылка на полное наименование закона, без изменений обработки/согласия.
- docs/CHECKSITE-2026-11-09.md: фактический разбор скриншотов, источники, проверки/ограничения.
- existing tests use tests/build_fixture.py isolated build. Reuse root node_modules via NODE_PATH or junction only outside tracked source if needed.

## Затронутые проверки

python tests/seo.test.py; python tests/catalog.test.py; python tests/test_audit_improvements.py; node --test tests/analytics.test.mjs tests/app.test.mjs; git diff --check. Не создавать общий wrapper. Узкие тесты после конкретного исправления. Проверки метатегов/баннера не подменяют реальную визуальную проверку. Исходный backend не меняется, PHP suite не нужен.

## Дополнение 10 ноября

Разрешены чистые stdlib функции/парсер HTML main→Markdown и llms index в существующем seo.py, подключение в build.py при необходимости, MIME/noindex .md в apache_config.py и небольшие тесты. Новый runtime Python-модуль не нужен: существующие fixture копируют seo.py, сохраняем этот шов. Имена API исполнитель выбирает в одном контексте, контракт: полученный content main + canonical URL → UTF-8 Markdown без интерактивных блоков; все обычные path→same-dir index.md кроме404; HTML-discovery ссылки и llms.txt только на созданные targets. Нельзя менять предыдущую принятую прозу, таблицы фактов, consent/CSP/backend/robots. Производный Markdown сохраняет факты таблиц и связи источников; новые технические утверждения не создаются. До преобразования прочитать editorial/PRODUCT_STANDARD.md, editorial/README.md, editorial/ARTICLE_STANDARD.md, чтобы сохранить контентные ограничения; переписывать материалы не требуется.

Затронутый новый checkset: python tests/agent_content.test.py (или один аналогичный файл выбранного имени), python tests/seo.test.py, python tests/catalog.test.py, python -m unittest discover -s tests -p test_apache_config.py; реальный existing httpd_routing_integration.py при изменении .htaccess. Новых JS изменений нет, повтор 41 app/analytics tests не нужен. Build/package в изолированной копии; source state не перезаписывать. В production новая инструкция пользователя разрешает публикацию объединённого результата, отдельный вопрос не требуется.

Если для согласованного MIME/noindex новых .md нужен узкий parity fix demo-worker, разрешены src/worker-runtime.mjs (только headers .md) и соответствующие tests/routing.test.mjs; запустить node --test tests/routing.test.mjs. API и security policy не менять. build.py должен явно включать text .md с корректным MIME вместо binary fallback, если стандартная mimetypes база платформы этого не гарантирует.
