# Контур испытаний и варианты провайдера

Дата проверки официальных источников: 2026-10-07. Провайдер текущего production уже выбран: REG.RU. Смена провайдера, PostgreSQL и новый S3 не одобрены и не выполнены. Для первоначального production-подобного теста при сохранении инфраструктуры используем отдельный REG.RU-контур; cloud-генератор может находиться у другого провайдера.

## Сохранить REG.RU

Плюсы: тот же PHP/MySQL/SMTP и минимальные изменения приложения. Условия репрезентативности: отдельные credentials/БД/сессии/cron, синтетические заявки и почтовый приёмник; подтверждённые CPU/RAM, квоты PHP процессов/БД и изоляция от действующего аккаунта. Понадобятся метрики, доступные на конкретном тарифе. Совпадение программной среды без сравнимых лимитов ресурсов не означает эквивалентную производительность.

На существующем shared hosting нельзя обещать горизонтальное масштабирование и 5000 успешных записей/сек. Если провайдер не предоставляет требуемую изоляцию/наблюдаемость, решение о отдельном VPS/облаке согласуется отдельно. Переезд на REG.RU VPS изменит топологию относительно shared production, что явно отражается в отчёте.

## DigitalOcean App Platform и Yandex Serverless Containers

| Критерий | DigitalOcean App Platform | Yandex Serverless Containers |
|---|---|---|
| Исполнение | Управляемые web services, workers, deployment/scheduled jobs | Контейнеры по HTTP/вызовам; масштабирование по вызовам, provisioned instances для холодного старта |
| Горизонтальное масштабирование | Ручное; CPU auto на dedicated; request-based auto на shared/dedicated. Request metrics учитывают окно 5 минут | concurrency и лимиты экземпляров/одновременных вызовов. До теста поднять квоты, сравнить cold/warm поведение |
| Файлы и состояние | Локальный FS непостоянный, volumes отсутствуют | Локальная запись теряется при остановке; фоновая работа обычного экземпляра без активных вызовов может приостанавливаться |
| Cron/почта | Есть отдельные workers. Scheduled jobs не чаще 15 минут, текущий retry каждые 5 минут напрямую не переносится | Timer trigger умеет минутное расписание; cron выражение UTC. Для долгих worker нужны явно выбранные режим/служба, не полагаться на фон HTTP контейнера |
| DB/S3 | Managed MySQL/PostgreSQL, Spaces S3-compatible; для текущего приложения MySQL проще | Managed MySQL/PostgreSQL, Object Storage S3-compatible; для текущего приложения MySQL проще |
| География | В списке App Platform регионов нет России | Для рассматриваемого решения выбрать регион Россия; проверить также backup и почтовую обработку |
| Критический контракт приложения | Общие сессии и trusted proxy IP вместо локальных файлов/сырого REMOTE_ADDR | Всё слева плюс документация HTTPS-вызова перечисляет Cookie среди удаляемых request headers. Сессионный CSRF нельзя считать совместимым без проверки маршрута и адаптации |
| Экономика | Оплата размеров/числа компонентов; workers и DB образуют постоянный минимум | Оплата вызовов, CPU/RAM execution, простоя подготовленных экземпляров и трафика. Managed DB/общие сессии остаются постоянной статьёй |

Источники исполнения/масштабирования: [DO limits](https://docs.digitalocean.com/products/app-platform/details/limits/), [DO scale](https://docs.digitalocean.com/products/app-platform/how-to/scale-app/), [YC lifecycle](https://yandex.cloud/en/docs/serverless-containers/concepts/container), [YC runtime](https://yandex.cloud/en/docs/serverless-containers/concepts/runtime), [YC quotas](https://yandex.cloud/ru/docs/serverless-containers/concepts/limits).

Дефолтные YC квоты включают по 10 экземпляров и 10 одновременных запросов на зону; это не предел RPS и не доказательство, что квоты аккаунта такие же. При 5000 RPS и среднем времени обработки 100 мс нужно ориентировочно 500 одновременных запросов по закону Little, плюс запас; до испытаний проверить реальные квоты/распределение и согласовать повышение. [Квоты](https://yandex.cloud/en/docs/serverless-containers/concepts/limits).

Контракт cookies и клиентского IP: [YC invoke](https://yandex.cloud/ru/docs/serverless-containers/concepts/invoke). Возможность сохранить нужный session/CSRF контракт через конкретную схему gateway ещё не доказана. Не устранять CSRF ради запуска контейнера. [Cron DO](https://docs.digitalocean.com/products/app-platform/how-to/manage-jobs/), [Timer YC](https://yandex.cloud/ru/docs/serverless-containers/concepts/trigger/timer).

В приложении `Orders::configured()` прямо требует russian_infrastructure_confirmed=true. DigitalOcean не является заменой для текущего российского контура без пересмотра этой архитектурной предпосылки и решения владельца. [Регионы DO](https://docs.digitalocean.com/products/app-platform/details/availability/). Это проверка существующего контракта приложения, не юридическое заключение.

## Стоимость и рост

Для масштаба цен, не готовой сметы: минимальные DO web $5/мес, single-node MySQL Standard $15/мес, Spaces $5/мес дают $25/мес только за эти три позиции. План web за $5 не поддерживает несколько экземпляров, single-node DB не даёт HA; worker, общий session store, VM генератора, трафик и резервирование в эту сумму не входят. Нельзя называть её достаточной инфраструктурой для 5000 RPS. [App pricing](https://docs.digitalocean.com/products/app-platform/details/pricing/), [MySQL pricing](https://docs.digitalocean.com/products/databases/mysql/details/pricing/), [Spaces pricing](https://docs.digitalocean.com/products/spaces/details/pricing/).

Важный момент на дату исследования: DO сообщает изменения Standard MySQL/PostgreSQL с 15 октября 2026 для аккаунтов, ещё не создававших такие кластеры, и с 30 ноября для всех аккаунтов: новые Standard кластеры не смогут брать планы свыше 4 GiB и standby/read replicas; существующие кластеры не затрагиваются. Следовательно, путь «маленький tier, потом больше» нужно проверять для конкретной edition и аккаунта, включая переход в Advanced, а не обещать бесшовный рост по старому прайс-листу. [Официальное объявление DO](https://docs.digitalocean.com/products/databases/).

YC публикует RUB формулу Serverless Containers: 3,79 ₽/GB-hour + 5,69 ₽/vCPU-hour + 18,97 ₽/миллион вызовов, с free tier и отдельно учитываемыми provisioned idle/egress. Полная смета зависит от concurrency/длительности, DB, дисков/backup, gateway, session store, registry/logs и VM; считать её по утверждённой конфигурации и валюте договора. [SC pricing](https://yandex.cloud/ru/docs/serverless-containers/pricing), [MySQL pricing](https://yandex.cloud/ru/docs/managed-mysql/pricing), [PostgreSQL pricing](https://yandex.cloud/ru/docs/managed-postgresql/pricing).

S3 сейчас не вызывается backend; добавлять его в нагрузочный путь ради того, что он есть у провайдера, не нужно. Его возможная роль после отдельного решения: статические ассеты, артефакты теста, backup и неизменяемые версии согласия. [YC S3](https://yandex.cloud/en/docs/storage/).

## Предварительная рекомендация

Для baseline сохранить REG.RU и воспроизвести действующий PHP/MySQL backend отдельно. Если владелец выбирает миграцию и российское размещение остаётся требованием, рассматривать Yandex Cloud с Managed MySQL; Serverless Containers принимать только после решения cookies/CSRF, proxy и worker-контрактов. Альтернатива внутри YC - обычные небольшие VM с PHP-FPM и балансировщиком, если она окажется проще и дешевле; это дополнительный вариант, не уже принятое решение.

DO удобен как PaaS с постоянными web/worker компонентами, если география допустима, доступен биллинг и учтён путь роста DB edition. Облачный вариант не должен автоматически означать PostgreSQL: текущие миграции поддерживают MySQL/SQLite; PostgreSQL потребует отдельного проекта с DDL/upsert/sequence/lease/ошибками/экспортом и проверкой переноса данных.

Запрошены у владельца: смысл RPS и доля записи; бюджеты теста/production; сохранить REG.RU или мигрировать; обязательность РФ; существующие аккаунты. Без ответов выбор и платное создание ресурсов не выполняются.
