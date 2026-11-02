# Product feed preparation — 2026-11-02

Scenario: submit the existing 64-product feed to Yandex Products. The published
`/yandex-products.xml` is accessible, but its date lacks the timezone required by
the current Yandex feed specification. Generate an RFC 3339 UTC timestamp;
preserve every product, price, stock value, URL, description and image.

Affected checks: the existing five generated-flow tests, including parsing the
feed date with a timezone and checking the 64 offers against the catalog. Live
validation of all 64 offers against current product HTML/JSON-LD and image GETs
passed for SKU, name, price, currency, availability, brand, category and canonical.

Publication scope is only `public_html/yandex-products.xml`. The release package
preserves the other 206 files from the verified 2026-11-01 production baseline.
The established file-only deployment guard retains its logic; only exact
baseline/package hashes and the verified 207-file inventory are rebound.

Feed registration is separate from publication. GET Products `feeds-info`
returned HTTP 403; local-browser access is disabled in Work settings, and the
separate browser redirects to Yandex sign-in. No registration receipt is claimed.
No IndexNow resubmission or paid API requests are included.

Evidence and final operational receipts:
`C:/Users/Alexandr/seo-audits/engine.cmteh.ru/evidence/yandex-feed-2026-11-02/`.

Official references:
- https://yandex.ru/support/merchants/ru/connect/form-feed
- https://yandex.ru/support/merchants/ru/connect/feed-load
- https://yandex.ru/dev/products/doc/ru/concepts/authorization
- https://yandex.ru/dev/webmaster/doc/ru/concepts/migration-guide
