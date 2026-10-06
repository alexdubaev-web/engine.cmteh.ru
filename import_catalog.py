"""Import the source XLSX into products.json (requires openpyxl)."""
import argparse
import collections
import json
import re
from pathlib import Path

from pipeline_io import pipeline_lock

ROOT = Path(__file__).resolve().parent


def parse_catalog(path):
    import openpyxl
    workbook = openpyxl.load_workbook(path, data_only=True)
    items = []
    for idx, row in enumerate(workbook.active.values, 1):
        if idx < 7 or not row[8]:
            continue
        codes = list(dict.fromkeys(str(row[2]).strip().split()))
        codes = [code for code in codes if code not in ['GMDAT', 'JCB444', '68.6KW']]
        name, brand, sku = row[8].strip(), row[10].strip(), codes[0]
        if 'ТНВД' in name or 'высокого давления' in name:
            category = 'pumps'
        elif 'Клапан' in name or 'клапан' in name:
            category = 'valves'
        elif name.startswith(('Распылитель', 'Комплект распылителя')):
            category = 'nozzles'
        elif name.startswith(('Топливная форсунка', 'Насос-форсунка')):
            category = 'injectors'
        else:
            category = 'other'
        short = name
        for suffix in [' Bosch / Caterpillar', ' John Deere / Denso', ' Delphi / JCB', ' Bosch', ' Delphi', ' John Deere', ' Denso']:
            short = short.replace(suffix, '')
        slug = re.sub('[^a-z0-9-]', '-', sku.lower()).strip('-')
        items.append({'id': slug, 'sku': sku, 'codes': codes, 'name': name, 'shortName': short,
                      'brand': brand, 'category': category, 'price': row[4], 'crossBrand': row[11] or '',
                      'sourceRow': idx, 'sourceUrls': list(dict.fromkeys([x for x in [row[9], row[12]] if x])),
                      'image': None, 'imageSource': None})
    if len(items) != 58:
        raise ValueError(f'Expected 58 products, found {len(items)}')
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='Source workbook path')
    args = parser.parse_args()
    items = parse_catalog(args.file)
    with pipeline_lock(ROOT):
        target = ROOT / 'data/products.json'
        target.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Products:', len(items), 'Brands:', dict(collections.Counter(x['brand'] for x in items)),
          'Categories:', dict(collections.Counter(x['category'] for x in items)))


if __name__ == '__main__':
    main()
