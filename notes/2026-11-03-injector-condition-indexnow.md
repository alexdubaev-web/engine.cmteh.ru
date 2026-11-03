# IndexNow: выпуск 3 ноября 2026

Статья /articles/novaya-ili-vosstanovlennaya-forsunka/ опубликована через PR22.
Проверенный source ab970dd42ffd6cf554392a277753e7aba808eb26,
publication main 9d39a09f4ca0f5317903da5b5f3bdc01c21cced7.
209 установленных файлов проверены существующим guarded helper; все6 изменённых
публичных ресурсов совпали с пакетом побайтно по HTTPS. Проверены реальный текст,
WebP, прямые ссылки и обратная ссылка из статьи о подлинности, списки, canonical,
sitemap, robots, desktop1440/mobile390. Все64 товарные карточки сохранены побайтно.

После публичной проверки штатный tools/indexnow.py выполнил ровно один POST
на https://yandex.com/indexnow. Начало 2026-11-03T06:08:43.286372+00:00,
конец 2026-11-03T06:08:43.669412+00:00. Ответ HTTP200, body success=true,
SHA256 ответа 87a298e2f119e18b116642dd02169d821a314776cd887e08c6da7f87011c8ce4.
Перед POST сохранена эксклюзивная запись попытки; автоматических повторов нет.

Приняты ровно4 действительно изменённых HTML URL:

- https://engine.cmteh.ru/
- https://engine.cmteh.ru/articles/
- https://engine.cmteh.ru/articles/novaya-ili-vosstanovlennaya-forsunka/
- https://engine.cmteh.ru/articles/proverka-podlinnosti-forsunki-pered-pokupkoy/

Штатное подтверждение принятых поколений очистило urls и revisions; очередь
после ответа пуста. Каталог, sitemap и неизменённые статьи повторно не отправлялись.
HTTP200 подтверждает приём уведомления, а не включение URL в поиск или позиции.
Очередь не подтверждалась заранее и не считается квитанцией сама по себе.

Проверки notification-задачи: существующие5 тестов test_indexnow_queue.py PASS;
фактический accepted=true, один POST, exact4URL и пустая очередь подтверждены.
Изменены только фактическое подтверждение очереди и эта запись; повторные app-тесты,
build, deploy и новое ревью не нужны для неизменённого опубликованного продукта.
Никаких реальных заказов или искусственных целей аналитики не отправлено.

Полные attempt/response/result и предыдущая очередь сохранены в
D:/codex/!engine.cmteh.ru/.runtime/article-injector-condition-20261103/.
Журнал выпуска: C:/Users/Alexandr/.codex/editorial/engine-cmteh/runs/2026-11-03-injector-condition.json.
