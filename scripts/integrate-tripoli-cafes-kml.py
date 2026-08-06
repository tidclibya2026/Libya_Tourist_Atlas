import csv, html, json, math, re, unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; SOURCE=ROOT/'data/incoming/tripoli-cafes.kml'; OUTPUT=ROOT/'data/layers/tripoli-cafes.geojson'
EXISTING=[ROOT/'data/layers/cafes.geojson',OUTPUT,ROOT/'data/layers/food-drink.geojson']; NS={'k':'http://www.opengis.net/kml/2.2'}; TODAY=date.today().isoformat()
CONTROL=re.compile(r'[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]'); IMG=re.compile(r'<img\b[^>]*?src=["\']([^"\']+)',re.I); TAG=re.compile(r'<[^>]+>')

def clean(v):
 v=CONTROL.sub('',unicodedata.normalize('NFC',v or '')).replace('\xa0',' '); v=re.sub(r'\s+',' ',v).strip(' \t\r\n.-–—_|،؛')
 out=[]
 for x in v.split():
  if not out or x.casefold()!=out[-1].casefold(): out.append(x)
 return ' '.join(out)
def norm(v):
 v=clean(v).casefold().replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي'); return re.sub(r'[^\w\u0600-\u06ff]+','',v)
def fields(pm):
 out={}
 for d in pm.findall('.//k:ExtendedData/k:Data',NS):
  k,v=clean(d.get('name','')),clean(d.findtext('k:value',default='',namespaces=NS))
  if k and v: out[k]=v
 for d in pm.findall('.//k:ExtendedData//k:SimpleData',NS):
  k,v=clean(d.get('name','')),clean(d.text or '')
  if k and v: out[k]=v
 return out
def first(data,*keys):
 low={clean(k).casefold():clean(v) for k,v in data.items()}
 for k in keys:
  if low.get(k.casefold()): return low[k.casefold()]
 return ''
def desc_text(raw,data):
 explicit=first(data,'الوصف','description')
 raw=explicit or raw or ''; raw=re.sub(r'<img\b[^>]*>',' ',raw,flags=re.I); raw=re.sub(r'<br\s*/?>','\n',raw,flags=re.I); raw=html.unescape(TAG.sub(' ',raw))
 lines=[]
 for line in raw.splitlines():
  line=clean(line)
  if not line or re.search(r'https?://|googleusercontent|mymaps\.usercontent',line,re.I): continue
  lines.append(line)
 return '\n'.join(dict.fromkeys(lines)) or None
def parse(path):
 tree=ET.parse(path); parent={c:n for n in tree.iter() for c in n}; rows=[]
 for i,pm in enumerate(tree.findall('.//k:Placemark',NS),1):
  pt=pm.find('.//k:Point/k:coordinates',NS); coords=None
  if pt is not None and pt.text:
   try: z=pt.text.strip().split(','); coords=(float(z[0]),float(z[1]))
   except (ValueError,IndexError): pass
  folder=''; node=parent.get(pm)
  while node is not None:
   if node.tag.endswith('Folder'): folder=clean(node.findtext('k:name',default='',namespaces=NS)); break
   node=parent.get(node)
  data=fields(pm); raw=pm.findtext('k:description',default='',namespaces=NS); images=list(dict.fromkeys(html.unescape(x) for x in IMG.findall(raw or ''))); media=first(data,'gx_media_links')
  if media and media not in images: images.append(media)
  rows.append({'index':i,'name':clean(pm.findtext('k:name',default='',namespaces=NS)),'raw':raw,'description':desc_text(raw,data),'coords':coords,'style':clean(pm.findtext('k:styleUrl',default='',namespaces=NS)),'folder':folder,'extended':data,'geometry':'Point' if pt is not None else 'other','images':images})
 return rows
def distance(a,b):
 if not a or not b:return 10**9
 x1,y1,x2,y2=map(math.radians,[a[0],a[1],b[0],b[1]]); dx,dy=x2-x1,y2-y1; return 12742000*math.asin(math.sqrt(math.sin(dy/2)**2+math.cos(y1)*math.cos(y2)*math.sin(dx/2)**2))
def similarity(a,b):
 a,b=norm(a),norm(b)
 if not a or not b:return 0
 if a==b:return 1
 pairs=lambda s:{s[i:i+2] for i in range(max(1,len(s)-1))}; x,y=pairs(a),pairs(b); return 2*len(x&y)/max(1,len(x)+len(y))
def classify(name,description):
 t=f'{name} {description or ""}'.casefold()
 rules=[
 ('shisha_cafe','مقهى يقدم الشيشة','Shisha cafe',['شيشة','ارگيلة','أرقيلة','ارقيلة','shisha','hookah']),
 ('tea_house','بيت شاي','Tea house',['بيت شاي','tea house','bubble tea','ببل تي']),
 ('ice_cream_shop','مثلجات وآيس كريم','Ice cream shop',['آيس كريم','ايس كريم','ice cream','gelato','جيلاتو','مثلجات']),
 ('juice_bar','عصائر','Juice bar',['عصائر','عصير','juice']),
 ('bakery_cafe','مخبز ومقهى','Bakery cafe',['bakery cafe','مخبز ومقه','مخبوزات ومقه']),
 ('cafe_restaurant','مطعم ومقهى','Cafe restaurant',['مقهى ومطعم','مقهي ومطعم','كافيه ومطعم','cafe and restaurant','cafe & restaurant','caffe and resto','resto coffe']),
 ('dessert_cafe','مقهى وحلويات','Dessert cafe',['حلويات','sweets','sweet shop','cake','patisserie','سينابون','cinnabon']),
 ('specialty_coffee','قهوة مختصة','Specialty coffee',['قهوة مختصة','specialty coffee','espresso lab','espressolab']),
 ('traditional_cafe','مقهى شعبي أو تقليدي','Traditional cafe',['مقهى شعبي','مقهي شعبي','قهوة شعبية','مقهى الحاج','الحاج فتحي']),
 ('coffee_shop','مقهى وقهوة','Coffee shop',['coffee shop','coffee','coffe','caffè','caffe','قهوة','مطحن بن','تحميص وطحن القهوة']),
 ('cafe','مقهى','Cafe',['مقهى','مقهي','كافي','كافيه','cafe','café']),]
 for code,ar,en,terms in rules:
  if any(x in t for x in terms): return code,ar,en,1.0
 if any(x in t for x in ['مطعم','restaurant','burger','برجر','وجبات سريعة','fast food','مشاوي','سندوتش','بيتزا','دجاج']): return 'review_required','تحتاج مراجعة','Review required',.3
 if any(x in t for x in ['مشروبات','طعام','نادي القهوة']): return 'cafe_other','منشأة مقاهٍ أخرى','Other cafe establishment',.7
 return 'review_required','تحتاج مراجعة','Review required',.3
def existing_features():
 for p in EXISTING:
  if p.exists():
   try:return json.loads(p.read_text(encoding='utf-8')).get('features',[])
   except Exception:pass
 return []

source=parse(SOURCE); existing=existing_features(); old=[]
for f in existing:
 p=f.get('properties',{}); g=f.get('geometry') or {}; old.append({'id':p.get('id'),'name':p.get('name_ar') or p.get('name'),'coords':g.get('coordinates') if g.get('type')=='Point' else None,'p':p})
name_counts=Counter(norm(r['name']) for r in source if r['name']); coord_counts=Counter((round(r['coords'][0],7),round(r['coords'][1],7)) for r in source if r['coords']); used=set(); ids=set(); features=[]; paired=[]
serials=[int(m.group(1)) for r in old if r['id'] and (m:=re.fullmatch(r'LY-FNB-CAF-TRI-(\d+)',str(r['id'])))]; serial=max(serials or [0])
for r in source:
 candidates=[]
 for oi,o in enumerate(old):
  if oi in used or not o['id']:continue
  d,s=distance(r['coords'],o['coords']),similarity(r['name'],o['name'])
  if s==1 and d<=30:candidates.append((0,d,oi,'exact_match'))
  elif s>=.86 and d<=100:candidates.append((1,d,oi,'high_confidence_match'))
 if candidates:
  _,_,oi,match=sorted(candidates)[0]; o=old[oi]; used.add(oi); fid=o['id']; local=[x for x in o['p'].get('local_images',[]) if isinstance(x,str) and (ROOT/x.lstrip('/')).exists()]
 else: serial+=1; fid=f'LY-FNB-CAF-TRI-{serial:05d}'; match='new_feature'; local=[]
 ids.add(fid); ext=r['extended']; coords=r['coords']; code,sub_ar,sub_en,class_score=classify(r['name'],r['description']); valid=bool(coords and -180<=coords[0]<=180 and -90<=coords[1]<=90); inside=bool(valid and 12.7<=coords[0]<=13.6 and 32.5<=coords[1]<=33.1)
 city=first(ext,'المدينة','city'); address=first(ext,'العنوان','address'); contact=first(ext,'وسائل الاتصال'); phone=first(ext,'رقم الهاتف','الهاتف','phone') or None; website=contact if contact.startswith(('http://','https://')) else None
 name_en=first(ext,'الاسم باللغة الانجليزية','name_en','English Name') or None; image=r['images'][0] if r['images'] else None; provider='google_mymaps' if image and ('googleusercontent' in image or 'mymaps.usercontent.google.com' in image) else ('remote_other' if image else None); image_status='temporary_google_url' if provider=='google_mymaps' else ('available_remote' if image else 'no_image')
 services=None; required={'name':r['name'],'coordinates':inside,'classification':code!='review_required','district':None,'address':address,'phone':phone,'website':website,'opening_hours':None,'services':services,'license':None,'image':bool(local)}; completeness=round(100*sum(bool(v) for v in required.values())/len(required)); overall=round((1+(1 if inside else 0)+class_score+(.5 if phone or website else 0)+(1 if local else (.3 if image else 0)))/5,2); quality='verified' if completeness==100 and inside else 'high' if completeness>=70 and inside else 'medium' if completeness>=45 and inside else 'low' if inside else 'review_required'
 p={'id':fid,'name_ar':r['name'],'name_en':name_en,'name_normalized_ar':norm(r['name']),'translation_status':'available' if name_en else 'pending_review','category':'الطعام والشراب','subcategory_ar':sub_ar,'subcategory_en':sub_en,'facility_type_code':code,'municipality_ar':'طرابلس','municipality_en':'Tripoli','city_ar':city or 'طرابلس','city_en':'Tripoli','district_ar':None,'district_en':None,'address_ar':address or None,'address_en':None,'longitude':coords[0] if coords else None,'latitude':coords[1] if coords else None,'source':'Tripoli cafes team KML','source_kml':'data/incoming/tripoli-cafes.kml','source_record_index':r['index'],'description_ar':r['description'],'description_en':None,'phone':phone,'email':None,'website':website,'opening_hours':None,'price_level':None,'services_ar':services,'services_en':None,'serves_shisha':True if code=='shisha_cafe' else None,'has_outdoor_seating':None,'has_wifi':None,'status':'active','license_status':None,'data_quality_status':quality,'data_review_status':'review_required' if quality in ('low','review_required') or code=='review_required' else 'integrated','source_image_url':image,'source_image_provider':provider,'source_image_status':image_status,'local_images':local,'image_count':len(local),'created_at':TODAY,'updated_at':TODAY,'name_score':1 if r['name'] else 0,'coordinate_score':1 if inside else 0,'classification_score':class_score,'contact_score':.5 if phone or website else 0,'image_score':1 if local else (.3 if image else 0),'completeness_score':completeness/100,'overall_quality_score':overall,'data_completeness_percent':completeness,'missing_fields':[k for k,v in required.items() if not v],'match_status':match,'coordinate_review_status':'valid' if inside else ('outside_tripoli_review_required' if valid else 'invalid'),'coordinate_change_reason':None,'original_coordinates':list(coords) if coords else None}
 features.append({'type':'Feature','id':fid,'properties':p,'geometry':{'type':'Point','coordinates':list(coords)} if valid else None}); paired.append((r,p))
dupes=[]
generic={'cafe','coffee','مقهى','مقهي','كافي','كافيه'}
for i,a in enumerate(features):
 if not a['geometry']:continue
 for b in features[i+1:]:
  if not b['geometry']:continue
  pa,pb=a['properties'],b['properties']; d=distance(a['geometry']['coordinates'],b['geometry']['coordinates']); s=similarity(pa['name_ar'],pb['name_ar']); cls=''; na=norm(pa['name_ar'])
  if na not in generic and d<1 and s>=.9:cls='confirmed_duplicate'
  elif na not in generic and d<30 and s==1:cls='confirmed_duplicate'
  elif na not in generic and d<100 and s>=.86:cls='review_required'
  if cls:dupes.append([pa['id'],pa['name_ar'],pb['id'],pb['name_ar'],round(d,1),round(s,3),cls,'retain_and_review','Same brand at different locations is not merged automatically'])
OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps({'type':'FeatureCollection','name':'Tripoli cafes','metadata':{'source':'data/incoming/tripoli-cafes.kml','generated_at':TODAY,'feature_count':len(features)},'features':features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write_csv(path,header,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='') as h:w=csv.writer(h);w.writerow(header);w.writerows(rows)
inventory=[]
for r,p in paired:
 c=r['coords']; inventory.append([r['index'],r['name'],norm(r['name']),c[0] if c else '',c[1] if c else '',p['coordinate_review_status'],'available' if r['description'] else 'missing',r['images'][0] if r['images'] else '',p['source_image_status'],r['style'],r['folder'],'duplicate_name' if name_counts[norm(r['name'])]>1 else 'unique','duplicate_coordinate' if c and coord_counts[(round(c[0],7),round(c[1],7))]>1 else 'unique',p['match_status']])
write_csv(ROOT/'docs/layers/tripoli-cafes-kml-inventory.csv',['source_index','source_name','normalized_name','longitude','latitude','geometry_status','description_status','image_url','image_status','style_url','folder','duplicate_name_status','duplicate_coordinate_status','notes'],inventory)
write_csv(ROOT/'docs/layers/tripoli-cafes-final-inventory.csv',['id','name_ar','facility_type_code','district_ar','longitude','latitude','match_status','data_quality_status','completeness_percent','image_status'],[[p['id'],p['name_ar'],p['facility_type_code'],p['district_ar'] or '',p['longitude'],p['latitude'],p['match_status'],p['data_quality_status'],p['data_completeness_percent'],p['source_image_status']] for p in (f['properties'] for f in features)])
write_csv(ROOT/'docs/review/tripoli-cafes-duplicate-review.csv',['record_a_id','record_a_name','record_b_id','record_b_name','distance_meters','name_similarity','duplicate_classification','recommended_action','notes'],dupes)
write_csv(ROOT/'docs/review/tripoli-cafes-data-quality-review.csv',['id','name_ar','quality_status','completeness_percent','missing_fields','review_status','notes'],[[p['id'],p['name_ar'],p['data_quality_status'],p['data_completeness_percent'],'|'.join(p['missing_fields']),p['data_review_status'],'Complete official fields; verify ambiguous classifications'] for p in (f['properties'] for f in features) if p['missing_fields'] or p['data_review_status']=='review_required'])
types=Counter(f['properties']['facility_type_code'] for f in features); qualities=Counter(f['properties']['data_quality_status'] for f in features); confirmed=sum(x[6]=='confirmed_duplicate' for x in dupes); review=sum(x[6]=='review_required' for x in dupes); inside=sum(f['properties']['coordinate_review_status']=='valid' for f in features); outside=sum(f['properties']['coordinate_review_status']=='outside_tripoli_review_required' for f in features)
report=f'''# تقرير دمج طبقة مقاهي طرابلس

## الملخص

- نقاط المصدر: {len(source)}
- النقاط النهائية: {len(features)}
- العناصر المطابقة: {len(used)}
- العناصر الجديدة: {len(features)-len(used)}
- التكرارات المؤكدة للمراجعة: {confirmed}
- التكرارات التي تحتاج مراجعة: {review}
- داخل نطاق طرابلس: {inside}
- خارج النطاق وتحتاج مراجعة: {outside}
- سجلات تحتوي روابط صور: {sum(bool(r['images']) for r in source)}

## توزيع التصنيفات

{chr(10).join(f'- {k}: {v}' for k,v in sorted(types.items()))}

## جودة البيانات

{chr(10).join(f'- {k}: {v}' for k,v in sorted(qualities.items()))}

## الفجوات

يلزم استكمال الأحياء والعناوين وساعات العمل والخدمات والأسعار والترخيص والواي فاي والجلسات الخارجية من الوزارة والجهات التابعة. روابط Google وMy Maps محفوظة كمراجع مؤقتة ولم تُنزّل أو تُعرض تلقائيًا. لم تُدمج التكرارات أو فروع العلامات التجارية تلقائيًا.
'''; (ROOT/'docs/tripoli-cafes-kml-integration-report.md').write_text(report,encoding='utf-8')
print(f'CAFES_SOURCE_KML_EXISTS = {SOURCE.exists()}');print(f'CAFES_SOURCE_FILE_SIZE = {SOURCE.stat().st_size}');print(f'CAFES_SOURCE_PLACEMARKS_TOTAL = {len(source)}');print(f'CAFES_TOTAL_PLACEMARKS = {len(source)}');print(f'CAFES_WITH_VALID_POINT_GEOMETRY = {sum(r["geometry"]=="Point" and bool(r["coords"]) for r in source)}');print(f'CAFES_WITHOUT_COORDINATES = {sum(not r["coords"] for r in source)}');print(f'CAFES_WITH_IMAGES = {sum(bool(r["images"]) for r in source)}');print(f'CAFES_WITHOUT_IMAGES = {sum(not r["images"] for r in source)}');print(f'CAFES_WITH_DESCRIPTIONS = {sum(bool(r["description"]) for r in source)}');print(f'CAFES_WITHOUT_DESCRIPTIONS = {sum(not r["description"] for r in source)}');print(f'CAFES_DUPLICATE_NAMES = {sum(v-1 for v in name_counts.values() if v>1)}');print(f'CAFES_DUPLICATE_COORDINATES = {sum(v-1 for v in coord_counts.values() if v>1)}');print(f'CAFES_INVALID_COORDINATES = {sum(not r["coords"] or not(-180<=r["coords"][0]<=180 and -90<=r["coords"][1]<=90) for r in source)}');print(f'EXISTING_CAFE_FEATURES = {len(old)}');print(f'MATCHED_EXISTING_CAFES = {len(used)}');print(f'NEW_CAFE_FEATURES = {len(features)-len(used)}');print(f'PRESERVED_EXISTING_IDS = {len(used)}');print(f'DUPLICATE_IDS = {len(features)-len(ids)}');print(f'VALID_CAFE_COORDINATES = {inside}');print(f'OUTSIDE_TRIPOLI_REVIEW_REQUIRED = {outside}');print('COORDINATES_SWAPPED = 0');print('COORDINATES_CHANGED = 0');print(f'CAFES_DUPLICATES_CONFIRMED = {confirmed}');print(f'CAFES_DUPLICATES_REVIEW_REQUIRED = {review}')
for key in ['cafe','coffee_shop','traditional_cafe','tea_house','specialty_coffee','dessert_cafe','cafe_restaurant','shisha_cafe','juice_bar','ice_cream_shop','bakery_cafe','cafe_other','review_required']:print(f'{key.upper()}_COUNT = {types[key]}')
