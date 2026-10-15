# John Deere catalog expansion worklog

Implemented the six owner-approved additions from `.runtime/new-parts-20261015/approved-import.json`. The approved import contains RE543262, RE571640, DZ100212, DZ100221, DZ100217 and DZ100216; no existing catalog item was updated.

The two pumps are in `pumps`; the four Common Rail injection nozzle kits are in `injectors`. Prices, quantities, public copy, technical facts and source URLs follow the approved import. Each item has its own all-caps SKU and lower-case ID, only the SKU in its code list, a verified technical record checked 2026-10-15, manufacturer-image provenance, `InStock` availability and stock source-row attribution. The original stock metadata and 58 prior stock rows remain intact.

The legacy 58-row catalog importer now rejects an import that omits any current product ID before writing. Its parser format is unchanged. Tests cover both the atomic write failure and expanded-catalog preservation on missing IDs. Generated output reports 64 products, 64 photos and 87 pages. The home and catalog counts derive from product data, and injector category copy identifies John Deere kits.

Validation completed: `python build.py`; `python tests/seo.test.py`; `python tests/catalog.test.py`; `python tests/stock.test.py`; `python -m unittest discover -s tests -p test_catalog_atomic.py`; `npm test`; `git diff --check`.
