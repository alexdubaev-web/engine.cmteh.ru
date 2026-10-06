import json,re,urllib.request,urllib.parse,concurrent.futures,time,io
from pathlib import Path
import os,tempfile
from pipeline_io import atomic_write_text,pipeline_lock
from PIL import Image
import lxml.html
root=Path(__file__).parent
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
    im.thumbnail((750,750));dest=root/'public/assets'/('part-'+p['id']+'.webp')
    store_image(root,dest,im.convert('RGB'))
    print(sku,'FOUND',u,flush=True);return {'id':p['id'],'image':'/assets/'+dest.name,'imageSource':u,'imageOriginal':iu}
  except Exception:pass
 print(sku,'MISSING',flush=True);return {'id':p['id']}

def merge_results(root,results):
 old_file=root/'data/images.json'
 previous=json.loads(old_file.read_text(encoding='utf-8')) if old_file.exists() else []
 old={item['id']:item for item in previous}
 merged=[]
 for item in results:
  if item.get('image'):
   merged.append(item)
   continue
  prior=old.get(item['id'],{})
  image=prior.get('image','')
  local=(root/'public'/image.lstrip('/')) if image.startswith('/assets/') else None
  merged.append(prior if local and local.is_file() and prior.get('imageSource') else item)
 return merged

def store_image(root,dest,image):
 dest.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile(prefix='.image-stage-',suffix='.webp',dir=root,delete=False) as staged:staged_path=Path(staged.name)
 try:
  image.save(staged_path,format='WEBP',quality=87)
  with pipeline_lock(root):os.replace(staged_path,dest)
 finally:staged_path.unlink(missing_ok=True)

def main():
 products=json.loads((root/'data/products.json').read_text(encoding='utf-8'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(find,products))
 with pipeline_lock(root):
  merged=merge_results(root,results)
  atomic_write_text(root/'data/images.json',json.dumps(merged,ensure_ascii=False,indent=2))
 print('Total photos',sum('image' in x for x in merged),flush=True)

if __name__=='__main__':main()
