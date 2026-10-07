# Backend Load Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Подготовить реальный PHP backend, БД и почтовые задания к честному измерению 1000/3000/5000/10000 RPS на отдельном контуре и выбрать минимальную инфраструктуру по результатам.

**Architecture:** Сохранить статический сайт и транзакционную запись заявок в MySQL. Убрать SMTP из HTTP-пути, оставить durable outbox в БД и вынести обработку в отдельный процесс/триггер; обеспечить общий CSRF-контракт для нескольких API узлов. Конкретный провайдер и величина потока новых заявок выбираются владельцем до реализации зависимых частей.

**Tech Stack:** PHP 8.3, PDO MySQL, sodium, PHPMailer, существующая статика; Grafana k6 OSS на облачной Linux VM для последующих испытаний. PostgreSQL, Redis/Valkey, S3 вводятся только при обоснованном выборе соответствующего контракта.

**Spec:** `notes/2026-10-07-load-readiness.md`, `notes/2026-10-07-cloud-options.md` и запрос владельца от 2026-10-07.

## Global Constraints

- Сейчас только аудит/план. Backend правки начинаются после зелёного света владельца. Provisioning и тесты 1000/3000/5000/10000 RPS начинаются после последующего плана тестирования и отдельной команды на запуск.
- Существующий production не используется как цель нагрузочного теста. Изолировать учётные данные, БД, session store, очередь, cron, секрет шифрования, SMTP и домен.
- Только синтетические персональные данные; SMTP sink вместо массовых реальных писем. Отдельно эмулировать измеренные задержки/ошибки SMTP. Результат такого сценария не подтверждает лимиты реального почтового провайдера.
- Сохранить consent/Origin/CSRF, idempotency, серверные цены и шифрование. У production не ослаблять rate limit или durability.
- Не менять ассортимент, SEO/UI и unrelated dirty work. `notes/` хранит доказательства, `tasks/` появится после согласования декомпозиции.
- Не обещать 5000 RPS до измерения успешных операций, задержек, ошибок, состояния БД/очереди и самого генератора.

## Review Focus

- Параллельные одинаковые/разные intent с одним UUID: одна запись либо корректный 409, без ложных конфликтов и двойной записи.
- SMTP принял сообщение, worker упал до изменения статуса: повтор возможен; стабильный Message-ID, очередь не теряется, lease защищает обычную конкуренцию.
- GET CSRF на узле A, POST на B, restart одного узла: контракт сохраняется; неверный токен не принимается.
- Таймаут/разрыв после commit: повтор с тем же UUID подтверждает прежнюю запись; сервер не утверждает, что письма уже доставлены.
- Большая таблица, фоновая очистка и просроченные lease одновременно с записью: bounded batch, пригодные планы запросов, отсутствие удаления активных заявок.

## Этап 0. Решения владельца

- [ ] Определить RPS: все HTTP, dynamic API или новые успешные заявки. Зафиксировать пропорции config/POST/replay/reject/static и объём таблиц.
- [ ] Утвердить сохранение REG.RU либо целевую миграцию, географию и бюджеты. Если выбран новый движок PostgreSQL, сначала написать отдельный план миграции; данный MySQL-план не становится PG-планом автоматически.
- [ ] Утвердить p95/p99, допустимые ошибки, очередь/время доставки, RPO/RTO и допустимость пропусков в номерах. Непрерывная нумерация и 5000 новых записей/сек требуют отдельного решения, не скрытого изменения поведения.

## Этап 1. Корректность ошибок и измеримость

Проблема: SQLSTATE -> ложный 409; swallowed exceptions лишают диагностики. Почему: ошибки/повторы нельзя считать успешными записями и нельзя находить источник насыщения. Как: исправить классификацию в `Orders::accept`, добавить безопасные категории логов и correlation ID в API/CLI.

**Files:** `backend/app.php`, `backend/api/config.php`, `backend/api/orders.php`, `backend/api/common.php`, `backend/console.php`, `tests/backend.php`; новые изолированные MySQL integration tests в `tests/`.

**Interfaces:** Сохранить публичный результат accept: ok, requestId, orderNumber, createdAt, message. 409 только для реально существующего другого intent; ошибки сервера безопасны для клиента. Метрики разделяют accepted_new, accepted_replay, validation/rate rejection и infrastructure error.

- [ ] Добавить регрессии из `notes/2026-10-07-order-integrity-error.md`; разделить SQLite-only trigger fixtures и MySQL suite.
- [ ] Исправить обработку, проверить same-UUID concurrency на MySQL, rollback, искусственный duplicate number и deadlock/lock timeout. Bounded retry допустим только для подходящих transient SQL errors всей транзакции с тем же UUID; не повторять неопределённый commit вслепую.
- [ ] Проверить, что логи не содержат контактов, payload, SMTP password, cookies/CSRF или полного DSN. Логировать DB connect/transaction duration, SQL error category, worker result/queue lag, без requestId как высококардинального label метрики.
- [ ] Проверки: `php tests/backend.php` с явно подключённым SQLite; отдельный MySQL fixture runner на Linux с отдельной test DB; `php tests/backend-export.php`; синтаксис PHP и существующие relevant tests. Production DSN должен быть запрещён тестовым runner.

## Этап 2. HTTP без SMTP, управляемая обработка outbox

Проблема: синхронный send занимает API процессы, finite cron batch не заменяет high-throughput worker. Почему: p99 и рост очереди иначе зависят от внешнего SMTP. Как: ответ после записи; отдельный bounded worker/scheduled invocation с безопасным lease, graceful shutdown, backoff и метриками.

**Files:** `backend/app.php` (`deliver`, `sendMail`), `backend/api/orders.php`, `backend/console.php`, config examples, hosting docs, MySQL worker concurrency tests.

**Interfaces:** Сохранить существующие accept/export/mailMessage contracts и queue state в DB. Расширить CLI отдельной worker-командой с параметрами batch/idle/shutdown, сохранив mail:retry. На выбранном serverless исполнении оформить отдельный authenticated invocation/adapter, не публичный произвольный CLI endpoint.

- [ ] Добавить проверки concurrent workers, crash после claim/после SMTP, lease expiry и retry, недоступность SMTP и graceful termination.
- [ ] Настроить batch claims без herd на одни строки; учитывать возможности выбранной MySQL версии (SKIP LOCKED не переносить в 5.7). Сетевой send всегда вне транзакции.
- [ ] Отключать immediate_delivery только вместе с готовым worker и сигнализацией очереди. Проверить, что HTTP success зависит от DB commit, а не от SMTP.
- [ ] Приёмка: queue depth/oldest age измеряются, повтор с тем же UUID не дублирует заявку; worker backlog после ошибки восстанавливается. Throughput HTTP и drain rate почты документируются отдельно.

## Этап 3. Запросы, индексы и короткие транзакции

Проблема: config читает список заявок; outbox/purge/listing не имеют подходящих индексов. Почему: работа растёт с размером истории, тогда как тест пустой БД скрывает это. Как: `Orders::ready(): bool` с лёгкой schema/readiness проверкой вместо listing; versioned migrations индексов и bounded cleanup.

**Files:** `backend/app.php`, `backend/api/config.php`, `backend/console.php`, DB fixtures/tests.

- [ ] Зафиксировать старые EXPLAIN и длительность на seeded данных разных размеров и распределений статусов, включая почти всё sent и очередь retry.
- [ ] Подобрать индексы для created_at, expires_at и outbox по фактическому EXPLAIN; измерить write amplification и долгие блокировки. Readiness обязана продолжать fail closed при отсутствующей схеме.
- [ ] Перенести вычисления/шифрование за пределы блокировки общего счётчика, где это сохраняет атомарность и timestamps. Purge выполнять ограниченными batches, сохранив срок хранения и защиту lease.
- [ ] Приёмка: config не вызывает listing; миграции повторяемы, старые зашифрованные записи читаются, план запросов и стоимость записи задокументированы на выбранной БД.

## Этап 4. Контракт нескольких узлов

Проблема: файловый CSRF и REMOTE_ADDR относятся к одиночному хостингу. Почему: простой horizontal scale может дать 403/429 вместо производительности. Как: выбрать общий session store либо подписанный CSRF, задать доверенные proxy и ограничить DB concurrency.

**Files:** `backend/api/common.php`, `backend/api/orders.php`, конфигурация, deployment manifests/container definition для выбранной среды, API integration tests.

- [ ] После выбора провайдера проверить browser cookie/Origin/header round-trip, особенно YC filtering Cookie. Решение нельзя считать готовым из одного unit test.
- [ ] Проверить CSRF A->B, node replacement, forged token и spoofed X-Forwarded-For. Общий session store имеет bounded TTL и ограничения памяти/подключений; при его отказе fail closed.
- [ ] Задать лимит PHP процессов и DB connections: api_replicas * processes + workers + reserve < допустимый предел нашего DB tier. Подтвердить TLS для managed DB и доступ к CA, health/readiness/graceful drain и секреты вне image.
- [ ] Не включать постоянные PDO connections или pool без проверки поведения конкретного PHP runtime/DB. PgBouncer относится только к отдельно выбранному PostgreSQL.

## Этап 5. Условные изменения для большого потока новых заявок

Проблема: общий counter и повтор полного HTML согласия. Почему: 5000 новых записей/сек принципиально тяжелее 5000 просмотров. Как: только после решения этапа 0 заменить выдачу номера на native auto increment/sequence с уникальностью и согласованными пропусками; хранить неизменяемую версию согласия отдельно с hash/ref.

**Files:** `backend/app.php`, versioned DB migration, `backend/console.php`, export/mail tests и документы о данных.

- [ ] Проверить начальный номер больше исторического максимума, сохранность старых номеров и экспорта, concurrent allocation, rollback с пропуском и отсутствие reset после purge.
- [ ] Проверить immutable consent bytes/hash/version, экспорт старых embedded и новых referenced записей; документ живёт, пока на него ссылается хоть одна сохраняемая заявка. Это может быть таблица БД; S3 не обязателен.
- [ ] Приёмка: нет единственного пользовательского counter-row lock в каждой новой транзакции, evidence согласия полностью восстанавливается; результаты не выдаются за 5000 RPS до теста.
- [ ] Если цель - посещения и редкие заявки, этот этап можно отложить после baseline. Не менять нумерацию только ради общей HTTP цифры.

## Этап 6. Подготовить отдельный контур и окончательный план теста

После приёмки первоочередных этапов: одинаковая production версия приложения/настроек и manifest различий, isolated DB и worker, synthetic fixtures, SMTP sink c latency/failure profile, TLS/domain, метрики/логи, облачная VM генератора. Изменение DB версии/изоляции/flush/ресурсов отражается явно; текущий профиль и будущий durable профиль нельзя смешивать в одном выводе.

Для тестов предлагается k6 OSS и arrival-rate executors. Итерации не равны HTTP RPS: login/config/POST/replay считаются отдельно. Проверить фактически достигнутый RPS, dropped_iterations, unique accepted rows и очередь; 429/503 не объявлять выполнением цели. Калибровать генератор, не размещать его на API/DB узле. Один IP и production rate limit проверять отдельным сценарием; bypass только изолированный и согласованный.

**Следующий deliverable после доработок:** отдельный план с точными ресурсами/стоимостью, mix, seed size, ramp/hold/soak/recovery, SLA/stop conditions, cron overlap, DB/SMTP faults, 1000/3000/5000/10000 RPS и teardown. Сейчас этот план и результаты не выдаются за готовые. Запуск только после команды владельца.

**Документация после измерений:** minimal production configuration, измеренная безопасная ёмкость одного API узла/DB tier, правила horizontal API и vertical DB scaling, HA/backup/rollback, себестоимость и журнал находок в notes. Конкретные tiers выбираются по измерениям, не сразу под 5000 RPS.
