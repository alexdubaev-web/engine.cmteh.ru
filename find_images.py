import json,re,urllib.request,urllib.parse,concurrent.futures,time,io
from pathlib import Path
from PIL import Image
import lxml.html
root=Path(__file__).parent
products=json.loads((root/'data/products.json').read_text())
headers={'User-Agent':'Mozilla/5.0'}
def html(u):
 d=urllib.request.urlopen(urllib.request.Request(u,headers=headers),timeout=12).read();return lxml.html.fromstring(d.decode('utf-8',errors='replace'))
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
def find(p):
 sku=p['sku']; urls=[u for u in p['sourceUrls'] if urllib.parse.urlparse(u).path.count('/')>1 and 'shop.deere' not in u and 'boschaftermarket' not in u]
 # exact article category URLs on an established diesel parts catalog
 if p['category']=='injectors':urls.insert(0,'https://fuelparts.ru/catalog/forsunki/forsunka-'+p['brand'].split()[0].lower()+'-'+sku.lower()+'/')
 if p['category']=='pumps':urls.insert(0,'https://fuelparts.ru/catalog/tnvd/tnvd-'+p['brand'].split()[0].lower()+'-'+sku.lower()+'/')
 urls.append('https://pnm-parts.ru/catalog/'+p['brand'].split()[0].lower()+'/'+p['brand'].split()[0].lower()+'/'+sku.lower())
 for u in list(dict.fromkeys(urls))[:4]:
  try:
   h=html(u);title=' '.join(h.xpath('//title/text()')+h.xpath('//h1//text()'))
   if norm(sku) not in norm(title):continue
   candidates=h.xpath('//meta[@property="og:image"]/@content')
   if 'pnm-parts' in u:candidates+=h.xpath('//img[contains(@src,"cdn.pnm-parts.ru/images")]/@src')
   for img in candidates[:2]:
    if any(s in img.lower() for s in ['generic','no-image','nozzles.jpg','logo']):continue
    iu=urllib.parse.urljoin(u,img);raw=urllib.request.urlopen(urllib.request.Request(iu,headers=headers),timeout=10).read()
    im=Image.open(io.BytesIO(raw));
    if min(im.size)<110:continue
    im.thumbnail((750,750));dest=root/'public/assets'/('part-'+p['id']+'.webp');im.convert('RGB').save(dest,quality=87)
    print(sku,'FOUND',u,flush=True);return {'id':p['id'],'image':'/assets/'+dest.name,'imageSource':u,'imageOriginal':iu}
  except Exception:pass
 print(sku,'MISSING',flush=True);return {'id':p['id']}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(find,products))
(root/'data/images.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Total photos',sum('image' in x for x in results),flush=True)
