# Техническая информация для ассортимента engine.cmteh.ru

Дата исследования: 13 октября 2026 года. Изучены все 58 артикулов текущего каталога. Для 53 карточек добавлен 151 технический факт. Для пяти артикулов надёжного подтверждения характеристик не найдено.

Изменения подготовлены в рабочей ветке `codex/seo-wordstat-all-cards`. После исследования владелец разрешил commit, merge, push и deploy. Состояние публикации фиксируется в [журнале релиза](2026-10-13-technical-release.md).

## Что добавлено в карточки

Раздел «Технические данные»: тип и серия детали, конструкция, масса, напряжение, OEM-номера, подтверждённые примеры применения и направления замены - в зависимости от доступных сведений для конкретного артикула. Источники и издатели сохранены во внутренних технических данных, но не выводятся в карточке. Раздел присутствует в статическом HTML; в навигации карточки есть ссылка «Характеристики».

Основа исследования: документы Bosch, John Deere, Delphi и оригинальные технические справочники профильных специалистов (Merlin Diesel, Ditex и другие). Для каждого факта во внутренних данных сохранены ссылка и издатель; данные не представлены как производительское подтверждение, если это сторонний справочник. Использованы также архивные документы; дата проверки не означает, что документ выпущен в 2026 году. Примеры техники не заменяют проверку исполнения и серийного номера.

Спорные габариты, параметры целого семейства без связи с точным SKU, неподтверждённые аналоги и подозрительные значения массы исключены. Масса DZ112112 переведена из фунтов в килограммы с сохранением исходного значения.

## Исправления исходного каталога

См. [журнал расхождений](2026-10-13-technical-catalog-issues.md): полный OEM-номер 28308779, марка применения 28540276 и категория DZ111136. Цены, складские остатки, URL и изображения сохранены.

## Проверки

Узкая проверка текущего технического рендеринга:

```powershell
python tests/catalog.test.py
```

Проверка проходит для 81 HTML-страницы и 58 товаров, включая уникальные метаданные, корректные SKU/цены, внутренние ссылки и JSON-LD. Для технического раздела она сверяет видимые значения фактов и примечаний с production-данными, а source URL и их связь с фактами проверяет внутри JSON без требования видимых ссылок. Отдельная сверка всех 151 факта с исследовательскими записями прошла; в исходных товарах изменены только три согласованных поля.

`python tests/test_catalog_atomic.py` прошёл: реальная тестовая XLSX-таблица повторно импортируется с сохранением трёх исправлений и дополнительных корректных номеров. `git diff --check` прошёл. Независимая проверка выявила неверный URL источника и три каталожных противоречия; они исправлены и проверены ограниченным заключительным проходом.

В изолированной локальной сборке проверены мобильная карточка 0445020110 (390 px), десктопная RE526588 (1440 px) и карточка без подтверждённых характеристик 7210-0473. Таблица читается, горизонтального переполнения нет; у непроверенной позиции показана только просьба прислать данные для подбора, без фактов и даты проверки. Источники не отображаются в карточках. Локальный сервер показывал только статический сайт: PHP API и отправка заказов в эту визуальную проверку не входили.

## Артикулы без подтверждённых технических данных

- **260100-4010**: При подборе сверим по фото маркировки тип насоса, двигатель и применяемость.
- **5620004100**: При подборе сверим по фото маркировки точное обозначение: 5620004100 или 562000410.
- **260100-6010**: При подборе сверим по фото маркировки связь с OEM-номером и применяемость.
- **7210-0473**: При подборе сверим по фото маркировки тип детали и применяемость.
- **8980436870**: При подборе сверим по фото маркировки тип детали и её связь с номером Isuzu.

Для этих пяти карточек характеристики не выдумывались. Нужны читаемая маркировка, паспорт детали или подтверждённая документация производителя. Подробные поиски и ограничения сохранены в исследовательских JSON.

## Результат по каждому артикулу

### 0433175478 - Распылитель топливной форсунки

- Масса нетто: **0,026 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция распылителя: **Распылитель с сопловыми отверстиями**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).

### 7206-0460 - Электромагнитный клапан топливной системы

- Тип узла: **По каталогу Ditex: клапан управления распылителем; версия 7206-0460-12B1.**. [Источник](https://www.ditex.it/dms/sito_ditex/documenti/Listino%20Delphi%20-%20Ricambi.pdf).
- Применяемость: **По каталогу Oto Perk: Delphi Smart Injector для DAF Euro 5.**. [Источник](https://www.eurodiesel.com/uploads/pdf/2UNIT-INJECTOR-Catalog-Fast-Moving-Items-2019-pdf_1554203639.pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 28272472 - Топливная форсунка Common Rail

- Система впрыска: **По каталогу Merlin Diesel: Common Rail, DFI 1.5.2.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- OEM-номер: **По каталогу Merlin Diesel: Mercedes-Benz A6510702387.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).

### 0445020610 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **4,964 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Sisu Diesel 837073731**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).

### RE539764 - Электрический топливный насос 24 В

- Тип детали: **Топливный насос**. [Источник](https://shop.deere.com/uk/product/RE539764%3A-Fuel-Transfer-Pump%2C-Fuel-Filter-To-Engine/p/RE539764).
- Напряжение: **24 В**. [Источник](https://shop.deere.com/uk/product/RE539764%3A-Fuel-Transfer-Pump%2C-Fuel-Filter-To-Engine/p/RE539764).
- Масса по каталогу: **0,671 кг**. [Источник](https://shop.deere.com/uk/product/RE539764%3A-Fuel-Transfer-Pump%2C-Fuel-Filter-To-Engine/p/RE539764).
- Примеры моделей из каталога: **John Deere 250D, 260E, 350G, 724K; подбор по серийному номеру**. [Источник](https://shop.deere.com/uk/product/RE539764%3A-Fuel-Transfer-Pump%2C-Fuel-Filter-To-Engine/p/RE539764).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 260100-4010 - Топливная форсунка

Подтверждённых технических фактов не найдено.

При подборе сверим по фото маркировки тип насоса, двигатель и применяемость.

### 9323A270G - Топливный насос высокого давления (ТНВД)

- Тип насоса: **По каталогу Merlin Diesel: DP210.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).
- Применяемость: **По каталогу Merlin Diesel: JCB TC Full Rate, 74,5 кВт.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).
- OEM-номера: **По каталогу Merlin Diesel: JCB 320/06930 и 320/06739.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 28540276 - Топливная форсунка Common Rail

- Система впрыска: **По каталогу Merlin Diesel: Common Rail, DFI 1.5.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- OEM-номера: **По каталогу Merlin Diesel: Hyundai/Kia 33800-2A760, 33800-2A790.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- Справочный номер Delphi: **По каталогу Merlin Diesel: R00203D.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).

### 7206-0435 - Электромагнитный клапан топливной системы

- Тип узла: **По каталогу Ditex: актуатор в сборе системы E1; версия 7206-0435-12B1.**. [Источник](https://www.ditex.it/dms/sito_ditex/documenti/Listino%20Delphi%20-%20Ricambi.pdf).

### 28516849 - Топливоподкачивающий насос

- Тип узла: **По каталогу Ditex: подкачивающий насос в сборе; версия 28516849-12B1.**. [Источник](https://www.ditex.it/dms/sito_ditex/documenti/Listino%20Delphi%20-%20Ricambi.pdf).
- Привод: **По каталогу TW Diesel: 9 зубьев.**. [Источник](https://23223077.fs1.hubspotusercontent-na1.net/hubfs/23223077/Cat%C3%A1logo%20TW%20Diesel.pdf).

### 0445020208 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **11,58 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Применение по каталогу Bosch: **MAN 18t-Series, 26t-Series, 35t-Series**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch-product-spotlight-bx-common_rail_july-2021.pdf).
- Номер Bosch eXchange: **0986437350**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch-product-spotlight-bx-common_rail_july-2021.pdf).

### 0445020201 - Топливный насос высокого давления (ТНВД)

- Каталожное соответствие OE: **CNHTC 805011167**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).

### L229PBC - Распылитель топливной форсунки

- Для форсунки: **Delphi BEBE4C08001.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).
- Тип системы: **Электронная насос-форсунка EUI, серия E1.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).

### 0445120075 - Топливная форсунка Common Rail

- Масса нетто: **0,63 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Тип форсунки Bosch: **CRIN2-16**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).
- Распылитель: **0433171966 / DLLA137P1577**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch_common_rail_fuel_injection_system_chinese_oem_applications.pdf).
- Клапанный комплект: **F00RJ01278**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch_common_rail_fuel_injection_system_chinese_oem_applications.pdf).

### 0445020082 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **11,55 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Пример применения: **MAN TGX 18.680; D2868 LF02/LF05; 01.2008–05.2014**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).

### RE507959 - Топливный насос впрыска (ТНВД)

- Тип детали: **Насос впрыска топлива**. [Источник](https://shop.deere.com/uk/product/RE507959%3A-Fuel-Injection-Pump/p/RE507959).
- Масса по каталогу: **3,864 кг**. [Источник](https://shop.deere.com/uk/product/RE507959%3A-Fuel-Injection-Pump/p/RE507959).
- Примеры моделей из каталога: **John Deere 5E-850, 6B-954, 120D, 310J; подбор по серийному номеру**. [Источник](https://shop.deere.com/uk/product/RE507959%3A-Fuel-Injection-Pump/p/RE507959).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### L053PBC - Распылитель топливной форсунки

- Тип распылителя: **По каталогу Ditex: для Smart Injector; версия L053PBC-12B1.**. [Источник](https://www.ditex.it/dms/sito_ditex/documenti/Listino%20Delphi%20-%20Ricambi.pdf).

### 0433175518 - Распылитель топливной форсунки

- Масса нетто: **0,026 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция распылителя: **Распылитель с сопловыми отверстиями**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Форсунка в сборе: **Bosch 0432193419**. [Источник](https://www.boschautopartes.mx/documents/652389/7415360/digital_guia_rapida_diesel%2B2023_.pdf/c590e13c-bdc9-b30b-b45e-f57292ccddcb?t=1699397441663).
- Двигатель в каталоге: **Mercedes-Benz OM457LA**. [Источник](https://www.boschautopartes.mx/documents/652389/7415360/digital_guia_rapida_diesel%2B2023_.pdf/c590e13c-bdc9-b30b-b45e-f57292ccddcb?t=1699397441663).
- Система впрыска: **UPS - отдельный насос на цилиндр**. [Источник](https://www.boschautopartes.mx/documents/652389/7415360/digital_guia_rapida_diesel%2B2023_.pdf/c590e13c-bdc9-b30b-b45e-f57292ccddcb?t=1699397441663).

### 0445020334 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **7,34 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).

### 0445020110 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **8,592 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **ЯМЗ 53401111010**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Тип ТНВД: **CR/CP3HS3/L110/30-789S**. [Источник](https://semar-servis.ru/images/my/20220130/20220130.pdf).

### 28308779 - Топливная форсунка Common Rail

- Система впрыска: **По каталогу Merlin Diesel: Common Rail, DFI 1.5.2.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- OEM-номер: **По каталогу Merlin Diesel: Mercedes-Benz A6510703287.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).

### L017PBB - Распылитель топливной форсунки

- Для форсунки: **Delphi BEBE4B12004.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).
- Применяемость: **Volvo FH12, двигатель D12C-420; по каталогу Delphi 2015/2016.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).
- OEM-номер форсунки: **Volvo 3155040.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 0445120126 - Топливная форсунка Common Rail

- Каталожное соответствие OE: **Mitsubishi Heavy 32G6100010**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Тип форсунки Bosch: **CRIN2-L**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).
- Комплектация по каталогу Bosch: **Без уплотнительного кольца**. [Источник](https://ap-ecat.boschaftermarket.com/SG/en_SG/products/0445120126).

### 0445120072 - Топливная форсунка Common Rail

- Каталожное соответствие OE: **Mercedes-Benz ME225416**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Тип форсунки Bosch: **CRIN3-L**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).

### 5620004100 - Топливная форсунка

Подтверждённых технических фактов не найдено.

При подборе сверим по фото маркировки точное обозначение: 5620004100 или 562000410.

### 0445020540 - Топливный насос высокого давления (ТНВД)

- Тип ТНВД: **CR/CP4N1/L50/20**. [Источник](https://semar-servis.ru/images/my/20220130/20220130.pdf).
- Двигатель в документе изготовителя: **ЯМЗ-53443; подбор по исполнению**. [Источник](https://semar-servis.ru/images/my/20220130/20220130.pdf).

### DZ112112 - Комплект распылителя форсунки

- Тип детали: **Комплект распылителя**. [Источник](https://shop.deere.com/us/product/DZ112112%3A-Nozzle-Kit/p/DZ112112).
- Масса по каталогу: **около 0,695 кг (1,533 фунта по каталогу)**. [Источник](https://shop.deere.com/us/product/DZ112112%3A-Nozzle-Kit/p/DZ112112).
- Примеры моделей из каталога: **John Deere 8R 230, 8R 410, 8RT 310, 8RX 410; подбор по серийному номеру**. [Источник](https://shop.deere.com/us/product/DZ112112%3A-Nozzle-Kit/p/DZ112112).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники. Точный состав поставки нужно уточнить при заказе.

### 0445226092 - Топливная рампа Common Rail

- Замена по каталогу Bosch: **0445226190**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/br/downloads_19/pdf_9/catlogo_diesel_2018_pginas_espelhadas.pdf).
- Датчик давления: **Bosch 0281006325**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/br/downloads_19/pdf_9/catlogo_diesel_2018_pginas_espelhadas.pdf).
- Клапан ограничения давления: **Bosch 1110010024**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/br/downloads_19/pdf_9/catlogo_diesel_2018_pginas_espelhadas.pdf).

### 0445120728 - Топливная форсунка Common Rail

- Тип форсунки Bosch: **CRIN3-18**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).

### 0445120212 - Топливная форсунка Common Rail

- Масса нетто: **0,603 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Тип форсунки Bosch: **CRIN1**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).
- Двигатель в каталоге: **Cummins ISBe**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch_common_rail_fuel_injection_system_chinese_oem_applications.pdf).
- Распылитель: **0433175501 / DSLA143P5501**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch_common_rail_fuel_injection_system_chinese_oem_applications.pdf).
- Клапанный комплект: **F00RJ02130**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch_common_rail_fuel_injection_system_chinese_oem_applications.pdf).

### 260100-6010 - Топливная форсунка Common Rail

Подтверждённых технических фактов не найдено.

При подборе сверим по фото маркировки связь с OEM-номером и применяемость.

### 0445116059 - Топливная форсунка Common Rail

- Масса нетто: **0,372 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Тип форсунки Bosch: **CRI 3-18**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).
- Применение по каталогу Bosch: **Citroën Jumper; Fiat Ducato; Iveco Daily; Peugeot Boxer**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch-product-spotlight-bx-common_rail_july-2021.pdf).
- Номер Bosch eXchange: **0986435395**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch-product-spotlight-bx-common_rail_july-2021.pdf).
- Комплектация по каталогу Bosch: **Без уплотнительного кольца**. [Источник](https://ap-ecat.boschaftermarket.com/MY/en_MY/products/0445116059).

### DZ128161 - Топливный насос высокого давления (ТНВД)

- Тип детали: **Топливный насос**. [Источник](https://shop.deere.com/br/pt/product/DZ128161%3A-Bombade-combust%C3%ADvel/p/DZ128161).
- Масса по каталогу: **7,318 кг**. [Источник](https://shop.deere.com/br/pt/product/DZ128161%3A-Bombade-combust%C3%ADvel/p/DZ128161).
- Примеры моделей из каталога: **John Deere 7R 290, 7R 310, 8R 230, 8R 340; подбор по серийному номеру**. [Источник](https://shop.deere.com/br/pt/product/DZ128161%3A-Bombade-combust%C3%ADvel/p/DZ128161).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### RE526588 - Электронный блок управления двигателем (ЭБУ)

- Тип детали: **Электронный контроллер двигателя**. [Источник](https://shop.deere.com/uk/product/RE526588%3A-Engine-Controller%2C-12-Volts-24-Volts%2C-Level-16/p/RE526588).
- Напряжение: **12 / 24 В**. [Источник](https://shop.deere.com/uk/product/RE526588%3A-Engine-Controller%2C-12-Volts-24-Volts%2C-Level-16/p/RE526588).
- Исполнение: **Level 16**. [Источник](https://shop.deere.com/uk/product/RE526588%3A-Engine-Controller%2C-12-Volts-24-Volts%2C-Level-16/p/RE526588).
- Семейства двигателей: **PowerTech 3029, 4045, 6068; требуется проверка комплектации**. [Источник](https://shop.deere.com/uk/product/RE526588%3A-Engine-Controller%2C-12-Volts-24-Volts%2C-Level-16/p/RE526588).
- Масса по каталогу: **0,912 кг**. [Источник](https://shop.deere.com/uk/product/RE526588%3A-Engine-Controller%2C-12-Volts-24-Volts%2C-Level-16/p/RE526588).
- Восстановленное исполнение в каталоге: **REMAN SE502802**. [Источник](https://shop.deere.com/uk/product/RE526588%3A-Engine-Controller%2C-12-Volts-24-Volts%2C-Level-16/p/RE526588).

### 0445124036 - Топливная форсунка Common Rail

- Масса нетто: **0,807 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Iveco 5801906153**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Тип форсунки Bosch: **CRIN3-22**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).

### 0445020089 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **11,562 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Двигатели в каталоге: **КамАЗ 740.70–740.75, Euro 4**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).

### 0445020081 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **11,53 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Liebherr 10117814**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).

### L215PBC - Распылитель топливной форсунки

- Для форсунки: **Delphi BEBE4D24002.**. [Источник](https://pt.scribd.com/document/482216241/Kits-Delphi-parcial-pdf).
- Тип системы: **Электронная насос-форсунка EUI, поколение E3.18.**. [Источник](https://pt.scribd.com/document/482216241/Kits-Delphi-parcial-pdf).
- Применяемость: **Volvo FH13 с 2007 года, D13A; по буклету Delphi.**. [Источник](https://pt.scribd.com/document/482216241/Kits-Delphi-parcial-pdf).
- OEM-номер форсунки: **Volvo 21340612.**. [Источник](https://pt.scribd.com/document/482216241/Kits-Delphi-parcial-pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 0445124025 - Топливная форсунка Common Rail

- Масса нетто: **0,6 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Sisu Diesel 837074860**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Тип форсунки Bosch: **CRIN3-20**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).

### DZ128160 - Топливный насос высокого давления (ТНВД)

- Тип детали: **Топливный насос**. [Источник](https://shop.deere.com/product/DZ128160%3A-Fuel-Pump/p/DZ128160).
- Примеры моделей из каталога: **John Deere 6M 145, 6R 145, 7R 210, 6175R; подбор по серийному номеру**. [Источник](https://shop.deere.com/product/DZ128160%3A-Fuel-Pump/p/DZ128160).
- Каталожная замена: **Указан John Deere как замена DZ123516**. [Источник](https://shop.deere.com/uk/product/DZ123516%3A-Fuel-Injection-Pump/p/DZ123516).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 0445020606 - Топливный насос высокого давления (ТНВД)

- Замена по каталогу Bosch: **0445020610**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/br/downloads_19/pdf_9/catlogo_diesel_2018_pginas_espelhadas.pdf).
- Каталожное соответствие OE: **Fendt V837073731**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/br/downloads_19/pdf_9/catlogo_diesel_2018_pginas_espelhadas.pdf).

### 0445020611 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **4,517 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Sisu Diesel 837074805**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).

### 28229876 - Топливная форсунка Common Rail

- Система впрыска: **По каталогу Merlin Diesel: Common Rail, DFI 2.5.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- OEM-номер: **По каталогу Merlin Diesel: JCB 320/06827.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).
- Применяемость: **По каталогу Merlin Diesel: JCB, 4,8 л, 108 кВт, Tier 4.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### L158PBA - Распылитель топливной форсунки

- Для форсунки: **Delphi LJBB04101A.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).
- Применяемость: **JCB с системой DP210; по каталогу Delphi 2015/2016.**. [Источник](https://pt.scribd.com/document/378208391/357711909-262059083-Catalogo-Diesel-Delphi-2015-2016-pdf-pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 0445020508 - Топливный насос высокого давления (ТНВД)

- Применение по каталогу Merlin Diesel: **Case / New Holland**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2025/05/WAAS-2025-1.pdf).

### F00RJ02177 - Ремкомплект топливной форсунки Common Rail

- Назначение комплекта: **Уплотнения высокого давления Common Rail**. [Источник](https://ap-ecat.boschaftermarket.com/TH/th/search/product/result?ccode%5B0%5D=DS008&page=20&perPage=51&view=list).

### 0414701072 - Насос-форсунка

- Масса нетто: **1,735 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Scania 1943974**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Система впрыска: **UIS - насос-форсунка**. [Источник](https://ap-ecat.boschaftermarket.com/TH/th/search/product/result?ccode%5B0%5D=DS008&page=28&perPage=51&view=list).

### 28384974 - Топливный насос высокого давления (ТНВД) Common Rail

- Тип насоса: **По каталогу Merlin Diesel: Common Rail, применение GMDAT.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- OEM-номер: **По каталогу Merlin Diesel: 25187375.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- Справочные номера Delphi: **По каталогу Merlin Diesel: 9422A040A, 28318239.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).

### DZ100218 - Комплект топливной форсунки (распылитель)

- Тип детали: **Комплект распылителя топливной форсунки**. [Источник](https://shop.deere.com/uk/product/DZ100218%3A-Fuel-Injection-Nozzle-Kit/p/DZ100218).
- Масса по каталогу: **0,617 кг**. [Источник](https://shop.deere.com/uk/product/DZ100218%3A-Fuel-Injection-Nozzle-Kit/p/DZ100218).
- Примеры моделей из каталога: **John Deere 4730, 4830, 9560 STS, 9570 STS; подбор по серийному номеру**. [Источник](https://shop.deere.com/uk/product/DZ100218%3A-Fuel-Injection-Nozzle-Kit/p/DZ100218).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники. Точный состав поставки нужно уточнить при заказе.

### 28384976 - Топливный насос высокого давления (ТНВД) Common Rail

- Тип насоса: **По каталогу Merlin Diesel: Common Rail, применение GMDAT.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- OEM-номер: **По каталогу Merlin Diesel: 25187376.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).
- Справочные номера Delphi: **По каталогу Merlin Diesel: 28286124, 28318240.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/08/DELPHI-CV-INJECTOR-APPLICATION-GUIDE-2024-new-1-1.pdf).

### 7210-0473 - Клапан регулирования давления топлива HPV

Подтверждённых технических фактов не найдено.

При подборе сверим по фото маркировки тип детали и применяемость.

### 8980436870 - Клапан управления подачей топлива SCV

Подтверждённых технических фактов не найдено.

При подборе сверим по фото маркировки тип детали и её связь с номером Isuzu.

### 9323A260G - Топливный насос высокого давления (ТНВД)

- Тип насоса: **По каталогу Merlin Diesel: DP210.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).
- Применяемость: **По каталогу Merlin Diesel: JCB 444 TC Derate.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).
- OEM-номера: **По каталогу Merlin Diesel: JCB 320/06738, 320/06929.**. [Источник](https://www.merlindiesel.com/wp-content/uploads/2024/04/JCB-CROSS-REF-APPLICATION-GUIDE-2024.pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### 0445120385 - Топливная форсунка Common Rail

- Масса нетто: **1,12 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Каталожное соответствие OE: **Mercedes-Benz A4710700887**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/catalogs/diesel.pdf).
- Тип форсунки Bosch: **CRIN4-27**. [Источник](https://help.boschdiagnostics.com/DCI700/content/InjectorOverview.pdf).

### 0445020273 - Топливный насос высокого давления (ТНВД)

- Масса нетто: **7 кг**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Конструкция насоса: **Радиально-поршневая**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/it/xx_pdfs_28/price_list/listini_prezzi.pdf).
- Применение по каталогу Bosch: **Weichai**. [Источник](https://www.boschaftermarket.com/xrm/media/images/country_specific/za/services_20/download_teasers/diesel/product_communication/bosch_common_rail_fuel_injection_system_chinese_oem_applications.pdf).

### 9109-903 - Клапан регулировки подачи топлива Common Rail

- Тип клапана: **Дозирующий клапан на входе насоса IMV системы Common Rail.**. [Источник](https://wypalaniedpf.pl/wp-content/uploads/2024/02/Katalog-CommonRail-DDSX451EN.pdf).
- Назначение: **Регулирует подачу топлива в камеру высокого давления насоса по сигналу блока управления.**. [Источник](https://wypalaniedpf.pl/wp-content/uploads/2024/02/Katalog-CommonRail-DDSX451EN.pdf).
- Пример применяемости: **Ford Focus I 1.8 TDCi Lynx, 100 л.с., 09.2002–11.2004, Euro III.**. [Источник](https://wypalaniedpf.pl/wp-content/uploads/2024/02/Katalog-CommonRail-DDSX451EN.pdf).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### DZ111136 - Клапан управления подачей топлива ТНВД

- Тип детали: **Клапан управления всасыванием топливного насоса (SCV)**. [Источник](https://shop.deere.com/uk/product/DZ111136%3A-Fuel-Pump-Suction-Control-Valve/p/DZ111136).
- Масса по каталогу: **0,259 кг**. [Источник](https://shop.deere.com/br/pt/product/DZ111136%3A-Valvula-de-Controle-para-Controle-de-Fluxo-de-%C3%93leo-do-Sistema-Hidr%C3%A1ulico-para-Tratores-Agr%C3%ADcolas/p/DZ111136).
- Примеры моделей из каталога: **John Deere 7R 210, 8R 230, 210G, 524K; подбор по серийному номеру**. [Источник](https://shop.deere.com/br/pt/product/DZ111136%3A-Valvula-de-Controle-para-Controle-de-Fluxo-de-%C3%93leo-do-Sistema-Hidr%C3%A1ulico-para-Tratores-Agr%C3%ADcolas/p/DZ111136).
- Каталожная замена: **Указан John Deere как замена RE536278**. [Источник](https://shop.deere.com/us/product/RE536278%3A-Control-Valve/p/RE536278).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники.

### DZ10599 - Комплект капитального ремонта двигателя

- Тип детали: **Комплект капитального ремонта двигателя**. [Источник](https://shop.deere.com/uk/product/DZ10599%3A-Engine-Overhaul-Kit/p/DZ10599).
- Масса по каталогу: **48,988 кг**. [Источник](https://shop.deere.com/uk/product/DZ10599%3A-Engine-Overhaul-Kit/p/DZ10599).
- Примеры моделей из каталога: **John Deere 8245R, 8330, 9560 STS, S660; подбор по серийному номеру**. [Источник](https://shop.deere.com/uk/product/DZ10599%3A-Engine-Overhaul-Kit/p/DZ10599).

Перечень в каталоге не гарантирует совместимость: сверьте модификацию и серийный номер техники. Точный состав поставки нужно уточнить при заказе.
