import openpyxl,json,re,collections
from pathlib import Path
root=Path(__file__).parent
w=openpyxl.load_workbook('/tmp/codex-remote-attachments/01a1074b-bf2a-746b-aff2-12b736d81054/1396A9B6-BCF6-488F-9B9B-22DA87A327D2/1-09-14_русские_наименования_бренды.xlsx',data_only=True)
items=[]
for idx,r in enumerate(w.active.values,1):
 if idx<7 or not r[8]:continue
 codes=list(dict.fromkeys(str(r[2]).strip().split()))
 codes=[x for x in codes if x not in ['GMDAT','JCB444','68.6KW']]
 name=r[8].strip();brand=r[10].strip();sku=codes[0]
 if 'ТНВД' in name or 'высокого давления' in name:cat='pumps'
 elif 'Клапан' in name or 'клапан' in name:cat='valves'
 elif name.startswith('Распылитель') or name.startswith('Комплект распылителя'):cat='nozzles'
 elif name.startswith('Топливная форсунка') or name.startswith('Насос-форсунка'):cat='injectors'
 else:cat='other'
 short=name
 for suffix in [' Bosch / Caterpillar',' John Deere / Denso',' Delphi / JCB',' Bosch',' Delphi',' John Deere',' Denso']:
  short=short.replace(suffix,'')
 slug=re.sub('[^a-z0-9-]','-',sku.lower()).strip('-')
 items.append({'id':slug,'sku':sku,'codes':codes,'name':name,'shortName':short,'brand':brand,'category':cat,'price':r[4],'crossBrand':r[11] or '', 'sourceRow':idx,'sourceUrls':list(dict.fromkeys([x for x in [r[9],r[12]] if x])),'image':None,'imageSource':None})
assert len(items)==58
(root/'data/products.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
print('Products:',len(items),'Brands:',dict(collections.Counter(x['brand'] for x in items)),'Categories:',dict(collections.Counter(x['category'] for x in items)))
