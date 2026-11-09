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
