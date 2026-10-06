# СМ ТЕХНО

58 товаров, 81 статическая страница, оригинальные статьи, адаптивный интерфейс. Рабочая поставка для российского хостинга — статика + PHP 8.2/MySQL/SMTP. Контакты не собираются на публичном зарубежном демо Sites.

```sh
python build.py
python package_ru.py
```

Сборка без сторонних Python-зависимостей. `release-ru/public_html` — корень домена; соседний `release-ru/backend` должен быть закрыт от веб-доступа. Полная настройка: [docs/HOSTING-RU.md](docs/HOSTING-RU.md).

Для демо: `npm run build && npm start`. Worker из dist/server используется только для демонстрации, обработчик персональных данных в нём выключен независимо от переменных окружения.

Утилиты импорта и Python-проверки требуют Python 3.10+ и зависимости из `requirements-dev.txt` (`python -m pip install -r requirements-dev.txt`). Сама сборка и упаковка используют только стандартную библиотеку.

Проверки:

```sh
npm test
python tests/catalog.test.py
python tests/seo.test.py
python tests/stock.test.py
python tests/pipeline_io.test.py
python -m unittest discover -s tests -p "test_*.py"
node --test tests/routing.test.mjs
php tests/backend.php
```

PHP-зависимость PHPMailer v7.1.1 включена в backend/vendor с лицензией. Папку backend/config.php, ключи, SMTP-пароли и базы не коммитить. Политика и согласие являются заготовками; приём заявок выключен до настройки и утверждения документов владельцем.

SEO и действия в Яндекс Вебмастере: [docs/SEO-YANDEX.md](docs/SEO-YANDEX.md). Все 58 карточек имеют авторские описания, Product/Offer, уникальные метатеги и хлебные крошки. `python tests/seo.test.py` проверяет структуру и соответствие данным; он не предсказывает позиции в поиске. Реальные реквизиты/наличие задаются в `data/commerce.json`.

Наличие импортировано из `09-14.xlsx`: все 58 позиций, 453 единицы. Обновление: `python import_stock.py путь.xlsx --dry-run`, затем без `--dry-run` и пересборка. Количество является снимком предоставленного перечня и не резервируется при запросе.
