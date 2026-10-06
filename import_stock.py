#!/usr/bin/env python3
"""Import stock from user-supplied XLSX: article in C, integer quantity in D.
Only SKU/count are published; original foreign-language labels are discarded.
"""
from pathlib import Path,PurePosixPath
from decimal import Decimal,InvalidOperation
from datetime import datetime,timezone
import argparse,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'

def normalize(value):return re.sub('[^A-Z0-9]','',str(value).upper())
def read_rows(path,sheet_name=None):
 with zipfile.ZipFile(path) as z:
  strings=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   strings=[''.join(t.text or '' for t in si.findall('.//s:t',NS)) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
  rels={x.get('Id'):x.get('Target') for x in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  sheets=ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS)
  selected=next((s for s in sheets if sheet_name is None or s.get('name')==sheet_name),None)
  if selected is None:raise ValueError('Worksheet not found')
  target=rels[selected.get('{'+REL+'}id')];member=target.lstrip('/') if target.startswith('/') else str(PurePosixPath('xl')/target)
  rows=[]
  for row in ET.fromstring(z.read(member)).findall('s:sheetData/s:row',NS):
   cells={}
   for c in row.findall('s:c',NS):
    col=re.sub(r'\d','',c.get('r',''));value=c.findtext('s:v',default='',namespaces=NS)
    if c.get('t')=='s':value=strings[int(value)]
    elif c.get('t')=='inlineStr':value=''.join(t.text or '' for t in c.findall('.//s:t',NS))
    cells[col]=value.strip()
   rows.append((int(row.get('r')),cells))
  return selected.get('name'),rows

def match_rows(rows,products):
 primary={};aliases={};result={}
 for p in products:
  primary.setdefault(normalize(p['sku']),set()).add(p['id'])
  for code in p['codes']:aliases.setdefault(normalize(code),set()).add(p['id'])
 for number,cells in rows:
  article=cells.get('C','').strip();quantity=cells.get('D','').strip()
  if not article or not re.search('[A-Za-z0-9]',article):continue # header/totals
  if not quantity:raise ValueError(f'Row {number}: quantity is missing')
  tokens=[normalize(t) for t in re.split(r'[\s,;]+',article) if normalize(t)]
  candidates=set().union(*(primary.get(t,set()) for t in tokens))
  if not candidates:candidates=set().union(*(aliases.get(t,set()) for t in tokens))
  if len(candidates)!=1:raise ValueError(f'Row {number}: unknown or ambiguous article: {article}')
  try:value=Decimal(quantity)
  except InvalidOperation:raise ValueError(f'Row {number}: invalid quantity')
  if not value.is_finite() or value<0 or value!=value.to_integral_value() or value>100_000_000:raise ValueError(f'Row {number}: quantity must be a nonnegative integer')
  identifier=next(iter(candidates));count=int(value)
  if identifier in result:raise ValueError(f'Row {number}: duplicate product; do not silently add quantities')
  result[identifier]={'quantity':count,'sourceRow':number}
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('file');parser.add_argument('--sheet');parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
 source=Path(args.file);products=json.loads((ROOT/'data/products.json').read_text());sheet,rows=read_rows(source,args.sheet);items=match_rows(rows,products)
 if set(items)!={p['id'] for p in products}:raise ValueError('Not all catalog products matched; import aborted')
 now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
 stock={'sourceFile':'09-14.xlsx' if '09-14' in source.name else source.name,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'worksheet':sheet,'importedAt':now,'items':items}
 commerce=json.loads((ROOT/'data/commerce.json').read_text())
 for identifier,item in items.items():commerce['availability'][identifier]='InStock' if item['quantity']>0 else 'OutOfStock'
 if not args.dry_run:
  (ROOT/'data/stock.json').write_text(json.dumps(stock,ensure_ascii=False,indent=2)+'\n')
  (ROOT/'data/commerce.json').write_text(json.dumps(commerce,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'matched':len(items),'units':sum(v['quantity'] for v in items.values()),'inStock':sum(v['quantity']>0 for v in items.values()),'outOfStock':sum(v['quantity']==0 for v in items.values()),'dryRun':args.dry_run},ensure_ascii=False))

if __name__=='__main__':main()
