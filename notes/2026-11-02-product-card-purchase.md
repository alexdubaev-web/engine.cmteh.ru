# Product-card purchase guidance — 2026-11-02

Owner request: adapt the existing commercial cards for buying and matching the
actual stocked parts. Keep public pages free of editorial/image-verification
notes. Preserve the current64-SKU assortment, prices, quantities, URL identities,
technical facts, images, consent, backend and form acknowledgement behavior.

Implemented for all64 cards:
- typed selection guidance covering injectors, UIS, pumps, nozzles, valves,
  repair kits, rail, ECU and transfer pumps; individual priority-SKU guidance;
- the actual card's SKU in its inquiry placeholder and selection heading;
- invoice payment, VAT, contract/documents and Russian delivery information;
- full existing company payment/delivery terms on the card;
- relevant selection articles for each actual part type;
- cleaner first-screen price note, without editorial caveats.

State, warranty, exact kit contents and dispatch deadlines have not been invented.
Existing technical facts and all images remain unchanged. No new product URLs,
manufacturer-part equivalence claims or customer data integrations were added.

Checks: catalog/SEO pass for98 pages and64 products; all5 existing generated-flow
tests pass, with the subsequently expanded64-SKU inquiry-context case checked
separately. Desktop1440 and mobile390 checks found no overflow; the local cart
added0445020089 and retained its122040 RUB VAT-inclusive total. DZ10599 retained
its overhaul-kit meaning and appropriate ordering guides. No real order or
analytics conversion was sent. One fresh independent review found no issues.

Production package:207 files;101 changed (64 product pages, CSS, shared CSS cache
references in other HTML, sitemap lastmod and feed date). Backend/API, scripts,
images, robots and Apache configuration preserve the current verified baseline.
Existing deployment guard logic is unchanged; exact baseline/package constants
are rebound and checked separately. The build queues64 changed product URLs;
notification and acknowledgement require their own actual receipt after live
publication verification.

Evidence/operational receipts:
`C:/Users/Alexandr/seo-audits/engine.cmteh.ru/evidence/product-cards-2026-11-02/`.
