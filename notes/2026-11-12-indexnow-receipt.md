# IndexNow после публикации 11 и 12 ноября

После публичного PASS 12 ноября в06:23:59UTC штатный tools/indexnow.py однократно передал шесть изменённых HTML URL в https://yandex.com/indexnow. POST начат в06:24:26UTC; получен HTTP200 и ответ {"success":true}. SHA256 тела ответа `87a298e2f119e18b116642dd02169d821a314776cd887e08c6da7f87011c8ce4`. Это приём уведомления, не подтверждение включения страниц в поиск.

- https://engine.cmteh.ru/
- https://engine.cmteh.ru/articles/
- https://engine.cmteh.ru/articles/klapan-rampy-ili-tnvd/
- https://engine.cmteh.ru/articles/klapan-scv-ili-imv-podbor/
- https://engine.cmteh.ru/articles/protokol-proverki-forsunki/
- https://engine.cmteh.ru/articles/rastyot-uroven-masla-v-dizele/

Из очереди удалены только шесть точных принятых ревизий; остальные91URL и их revision tokens сохранены. Статья10ноября повторно не отправлялась; неизвестные старые отправки не повторялись. Канонические HTML URL обеих новых статей, их WebP, прямые/обратные ссылки, архив, sitemap и production robots проверены по фактическому содержимому и байтам пакета. Markdown имеет предусмотренный noindex и в запрос не включался.

Публичный исходник PR46:443e7e540e087736222dc5242fcbfe2c6d886bc5, merge603b0080db8060a92ccad9dc3ecd89e7e1dbf8e6. Пакет335payload SHA256 e6447d552cae22af8081440976f905ea56c034d8015bec134c2bbbf51738fb44. Квитанция, эксклюзивная запись попытки и точные токены: закрытый дневной `.runtime/article-20261112/indexnow-result.json`, `indexnow-response.json`, `indexnow-attempt.json`. Эта правка содержит только acknowledgment и журнал; повторная сборка и deploy публичных файлов не требуются.
