#!/usr/bin/env python3
"""Isolated reproductions for importer and IndexNow write races. No network access."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from types import ModuleType
import contextlib, io, json, os, runpy, shutil, sys, urllib.request

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def repro_images(root):
    case = root / 'images-case'
    (case / 'public' / 'assets').mkdir(parents=True)
    (case / 'data').mkdir()
    write_json(case / 'data' / 'products.json', [{
        'id': 'sku-1', 'sku': 'SKU-1', 'sourceUrls': ['https://example.test/path/item'],
        'category': 'other', 'brand': 'Bosch'
    }])
    write_json(case / 'data' / 'images.json', [{
        'id': 'sku-1', 'image': '/assets/known.webp', 'imageSource': 'https://known.test/item'
    }])
    shutil.copy2(REPO / 'find_images.py', case / 'find_images.py')

    # Stub optional parsers and force every attempted URL fetch to fail.
    pil = ModuleType('PIL'); pil.Image = object()
    lxml = ModuleType('lxml'); lxml.__path__ = []
    lxml_html = ModuleType('lxml.html'); lxml_html.fromstring = lambda _s: None
    old_modules = {k: sys.modules.get(k) for k in ('PIL', 'lxml', 'lxml.html')}
    old_urlopen = urllib.request.urlopen
    sys.modules.update({'PIL': pil, 'lxml': lxml, 'lxml.html': lxml_html})
    urllib.request.urlopen = lambda *a, **kw: (_ for _ in ()).throw(OSError('mocked network miss'))
    try:
        runpy.run_path(str(case / 'find_images.py'), run_name='__main__')
    finally:
        urllib.request.urlopen = old_urlopen
        for k, v in old_modules.items():
            if v is None: sys.modules.pop(k, None)
            else: sys.modules[k] = v
    result = json.loads((case / 'data' / 'images.json').read_text(encoding='utf-8'))
    print('find_images:', json.dumps({
        'beforeHadImage': True,
        'afterRecord': result[0],
        'existingImageMetadataLost': 'image' not in result[0]
    }, ensure_ascii=False))

def make_xlsx(path):
    workbook = '''<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Stock" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>'''
    sheet = '''<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="7"><c r="C7" t="inlineStr"><is><t>SKU-1</t></is></c><c r="D7"><v>2</v></c></row></sheetData></worksheet>'''
    with ZipFile(path, 'w') as z:
        z.writestr('xl/workbook.xml', workbook)
        z.writestr('xl/_rels/workbook.xml.rels', rels)
        z.writestr('xl/worksheets/sheet1.xml', sheet)

def repro_stock(root):
    case = root / 'stock-case'
    (case / 'data').mkdir(parents=True)
    shutil.copy2(REPO / 'import_stock.py', case / 'import_stock.py')
    write_json(case / 'data' / 'products.json', [{'id':'sku-1','sku':'SKU-1','codes':['SKU-1']}])
    original_commerce = {'availability': {'sku-1': 'OutOfStock'}}
    write_json(case / 'data' / 'commerce.json', original_commerce)
    xlsx = case / 'input.xlsx'; make_xlsx(xlsx)

    from pathlib import Path as RealPath
    original_write = RealPath.write_text
    def fail_second_write(self, data, *args, **kwargs):
        if self.name == 'commerce.json':
            raise OSError('mocked failure between the two publishes')
        return original_write(self, data, *args, **kwargs)
    RealPath.write_text = fail_second_write
    old_argv = sys.argv
    try:
        sys.argv = [str(case / 'import_stock.py'), str(xlsx)]
        ns = runpy.run_path(str(case / 'import_stock.py'), run_name='audit_import_stock')
        try: ns['main']()
        except OSError as exc: print('import_stock mocked failure:', str(exc))
    finally:
        RealPath.write_text = original_write
        sys.argv = old_argv
    stock = json.loads((case / 'data' / 'stock.json').read_text(encoding='utf-8'))
    commerce = json.loads((case / 'data' / 'commerce.json').read_text(encoding='utf-8'))
    print('import_stock:', json.dumps({
        'stockQuantity': stock['items']['sku-1']['quantity'],
        'availability': commerce['availability']['sku-1'],
        'consistent': (stock['items']['sku-1']['quantity'] > 0) == (commerce['availability']['sku-1'] == 'InStock')
    }))

def repro_indexnow(root):
    case = root / 'indexnow-case'
    (case / 'data').mkdir(parents=True)
    (case / 'tools').mkdir()
    script = case / 'tools' / 'indexnow.py'
    shutil.copy2(REPO / 'tools' / 'indexnow.py', script)
    state_path = case / 'data' / 'seo-changes.json'
    original = {'origin':'https://engine.cmteh.ru','indexable':True,'generated_at':'initial','urls':['https://engine.cmteh.ru/old/']}
    write_json(state_path, original)
    key = 'audit-key-1234'
    class Response:
        def __init__(self, body=b'', status=202): self.body = body; self.status = status
        def __enter__(self): return self
        def __exit__(self, *exc): return False
        def read(self, _n=-1): return self.body
    calls = []
    def mocked_urlopen(request, timeout=None):
        calls.append(request)
        if isinstance(request, str):
            return Response((key + '\n').encode(), status=200)
        # Simulate a successful concurrent build that adds a new pending URL.
        fresh = json.loads(state_path.read_text(encoding='utf-8'))
        fresh['urls'].append('https://engine.cmteh.ru/new-during-submit/')
        write_json(state_path, fresh)
        return Response()
    old_urlopen = urllib.request.urlopen
    old_argv = sys.argv
    old_key = os.environ.get('INDEXNOW_KEY')
    urllib.request.urlopen = mocked_urlopen
    os.environ['INDEXNOW_KEY'] = key
    sys.argv = [str(script), 'submit']
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output): runpy.run_path(str(script), run_name='__main__')
    finally:
        urllib.request.urlopen = old_urlopen
        sys.argv = old_argv
        if old_key is None: os.environ.pop('INDEXNOW_KEY', None)
        else: os.environ['INDEXNOW_KEY'] = old_key
    final = json.loads(state_path.read_text(encoding='utf-8'))
    print('indexnow mocked output:', output.getvalue().strip())
    print('indexnow:', json.dumps({
        'concurrentBuildAdded':'https://engine.cmteh.ru/new-during-submit/' in final.get('urls', []),
        'finalUrls': final.get('urls'),
        'concurrentAdditionLost': 'https://engine.cmteh.ru/new-during-submit/' not in final.get('urls', [])
    }))

with TemporaryDirectory(prefix='cmteh-audit-repro-', dir=BASE) as tmp:
    root = Path(tmp)
    repro_images(root)
    repro_stock(root)
    repro_indexnow(root)



