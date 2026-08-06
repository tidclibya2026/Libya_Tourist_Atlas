import csv, html, json, math, re, unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/incoming/tourist-villages-resorts.kml'
OLD_KML=ROOT/'data/kml/final/resorts.kml'
OUTPUT=ROOT/'data/layers/tourist-villages-resorts.geojson'
NS={'k':'http://www.opengis.net/kml/2.2'}; TODAY=date.today().isoformat()
CONTROL=re.compile(r'[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]')
IMG=re.compile(r'<img\b[^>]*?src=["\']([^"\']+)',re.I); TAG=re.compile(r'<[^>]+>')

def clean(v):
 v=CONTROL.sub('',unicodedata.normalize('NFC',v or '')).replace('\xa0',' ')
 v=re.sub(r'[_]{2,}|[^\w\s\u0600-\u06ff&+()/.،؛:\-]',' ',v)
 v=re.sub(r'\s+',' ',v).strip(' .-_،؛|')
 words=[]
 for word in v.split():
  if not words or word.casefold()!=words[-1].casefold(): words.append(word)
 return ' '.join(words)
def norm(v):
 v=clean(v).casefold().translate(str.maketrans('أإآةىؤئ','اااهيوي'))
 return re.sub(r'[^\w\u0600-\u06ff]+','',v)
def xdata(pm):
 out={}
 for node in pm.findall('.//k:ExtendedData/k:Data',NS):
  key=clean(node.get('name','')); value=node.findtext('k:value',default='',namespaces=NS) or ''
  if key and value.strip(): out[key]=value.strip()
 for node in pm.findall('.//k:ExtendedData//k:SimpleData',NS):
  key=clean(node.get('name','')); value=(node.text or '').strip()
  if key and value: out[key]=value
 return out
def extract_meta(raw,ext):
 text='\n'.join([raw or '',*ext.values()]); text=html.unescape(TAG.sub('\n',text)); out={}
 aliases={'name_en':['الاسم باللغة الانجليزية','english name'],'address':['العنوان/المدينة','العنوان','المدينة'],'phone':['للحجز والاستفسار','رقم الهاتف','الهاتف'],'website':['وسائل الاتصال','الموقع الإلكتروني'],'units':['عدد الشاليهات','عدد الوحدات'],'beds':['عدد الاسرة','عدد الأسرة'],'capacity':['الطاقة الاستيعابية'],'services':['الخدمات المتوفرة','الخدمات المتاحة']}
 for key,names in aliases.items():
  for label in names:
   m=re.search(r'(?:^|\n)\s*'+re.escape(label)+r'\s*:\s*([^\n]+)',text,re.I)
   if m and clean(m.group(1)): out[key]=clean(m.group(1)); break
 urls=re.findall(r'https?://[^\s<>"\']+',text,re.I)
 if urls and 'website' not in out: out['website']=urls[0].rstrip('.,؛')
 phones=re.findall(r'(?<!\d)(?:\+?218[-\s]?)?0?9\d(?:[-\s]?\d){7}(?!\d)',text)
 if phones and 'phone' not in out: out['phone']=clean(phones[0])
 return out
def description(raw):
 text=re.sub(r'<img\b[^>]*>',' ',raw or '',flags=re.I); text=re.sub(r'<br\s*/?>','\n',text,flags=re.I); text=html.unescape(TAG.sub(' ',text))
 lines=[]
 for line in text.splitlines():
  line=clean(line)
  if not line or re.search(r'https?://|googleusercontent|tessellate|visibility|extrude|^_+',line,re.I): continue
  if line not in lines: lines.append(line)
 return '\n'.join(lines) or None
def parse(path):
 tree=ET.parse(path); parent={c:p for p in tree.iter() for c in p}; rows=[]
 for i,pm in enumerate(tree.findall('.//k:Placemark',NS),1):
  point=pm.find('.//k:Point/k:coordinates',NS); coords=None
  if point is not None and point.text:
   try: parts=point.text.strip().split(','); coords=[float(parts[0]),float(parts[1])]
   except (ValueError,IndexError): pass
  folder=''; node=parent.get(pm)
  while node is not None:
   if node.tag.endswith('Folder'): folder=clean(node.findtext('k:name',default='',namespaces=NS)); break
   node=parent.get(node)
  raw=pm.findtext('k:description',default='',namespaces=NS) or ''; ext=xdata(pm); images=list(dict.fromkeys(html.unescape(x) for x in IMG.findall(raw)))
  for value in ext.values():
   for url in IMG.findall(value):
    if url not in images: images.append(html.unescape(url))
  rows.append({'index':i,'name':clean(pm.findtext('k:name',default='',namespaces=NS)),'raw':raw,'description':description(raw),'coords':coords,'style':clean(pm.findtext('k:styleUrl',default='',namespaces=NS)),'folder':folder,'extended':ext,'meta':extract_meta(raw,ext),'images':images,'geometry':'Point' if point is not None else 'other'})
 return rows
def dist(a,b):
 if not a or not b:return 1e12
 x1,y1,x2,y2=map(math.radians,[a[0],a[1],b[0],b[1]]); return 12742000*math.asin(math.sqrt(math.sin((y2-y1)/2)**2+math.cos(y1)*math.cos(y2)*math.sin((x2-x1)/2)**2))
def sim(a,b):
 a,b=norm(a),norm(b)
 if not a or not b:return 0
 if a==b:return 1
 pairs=lambda s:{s[i:i+2] for i in range(max(1,len(s)-1))}; x,y=pairs(a),pairs(b); return 2*len(x&y)/max(1,len(x)+len(y))
def classify(name,desc):
 t=f'{name} {desc or ""}'.casefold()
 rules=[('camping_resort','منتجع تخييم','Camping resort',['تخييم','مخيم','camping']),('eco_resort','منتجع بيئي','Eco resort',['بيئي','ecolodge','eco resort']),('mountain_resort','منتجع جبلي','Mountain resort',['جبلي','الجبل','mountain']),('desert_resort','منتجع صحراوي','Desert resort',['صحراوي','الصحراء','desert']),('beach_resort','منتجع شاطئي','Beach resort',['شاطئي','الشاطئ','بحري','sea resort','شاطئ خاص']),('family_resort','منتجع عائلي','Family resort',['عائلي','للعائلات','family resort']),('holiday_village','قرية عطلات','Holiday village',['قرية عطلات','holiday village']),('tourist_complex','مجمع سياحي','Tourist complex',['مجمع سياحي','مركب سياحي','tourist complex']),('tourist_village','قرية سياحية','Tourist village',['قرية سياحية','القرية السياحية']),('tourist_resort','منتجع سياحي','Tourist resort',['منتجع سياحي','المنتجع السياحي','tourist resort','resort'])]
 for code,ar,en,terms in rules:
  if any(term in t for term in terms): return code,ar,en,1.0
 if any(term in t for term in ['قرية سكنية','فندق','hotel']) and not any(term in t for term in ['منتجع','سياحي','resort']): return 'review_required','تحتاج مراجعة','Review required',.25
 if any(term in t for term in ['شاليه','مصيف','استراحة سياحية']): return 'accommodation_resort_other','منشأة سياحية أخرى','Other tourism accommodation',.65
 return 'review_required','تحتاج مراجعة','Review required',.25
def city_region(text,coords):
 cities=[('طرابلس','Tripoli','طرابلس','Tripoli','TRI'),('بنغازي','Benghazi','برقة','Cyrenaica','BEN'),('مصراتة','Misrata','مصراتة','Misrata','MIS'),('زوارة','Zuwara','الساحل الغربي','Western Coast','ZUW'),('الخمس','Khoms','المرقب','Al Marqab','KHO'),('صبراتة','Sabratha','الساحل الغربي','Western Coast','SAB'),('غدامس','Ghadames','فزان','Fezzan','GHA'),('غات','Ghat','فزان','Fezzan','GHT'),('سبها','Sabha','فزان','Fezzan','SEB'),('درنة','Derna','برقة','Cyrenaica','DER'),('طبرق','Tobruk','برقة','Cyrenaica','TOB'),('البيضاء','Al Bayda','برقة','Cyrenaica','BAY'),('شحات','Shahhat','برقة','Cyrenaica','SHA'),('زليتن','Zliten','المرقب','Al Marqab','ZLI')]
 for ar,en,rar,ren,code in cities:
  if ar in text:return ar,en,rar,ren,code
 return None,None,None,None,'NAT'
def num(v):
 m=re.search(r'\d+',v or ''); return int(m.group()) if m else None
def write_csv(path,header,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='') as f: w=csv.writer(f); w.writerow(header); w.writerows(rows)

source=parse(SOURCE); old=parse(OLD_KML) if OLD_KML.exists() else []
name_counts=Counter(norm(r['name']) for r in source if r['name']); coord_counts=Counter(tuple(round(x,7) for x in r['coords']) for r in source if r['coords'])
matched_old=set(); match_by_index={}
for r in source:
 candidates=[]
 for j,o in enumerate(old):
  d,s=dist(r['coords'],o['coords']),sim(r['name'],o['name'])
  if s==1 and d<=30:candidates.append((0,d,j,'exact_match'))
  elif s>=.86 and d<=100:candidates.append((1,d,j,'high_confidence_match'))
 if candidates:
  _,_,j,status=sorted(candidates)[0]; matched_old.add(j); match_by_index[r['index']]=status
serials=defaultdict(int); features=[]; paired=[]
for r in source:
 coords=r['coords']; valid=bool(coords and -180<=coords[0]<=180 and -90<=coords[1]<=90); inside=bool(valid and 9<=coords[0]<=26 and 19<=coords[1]<=34)
 if not (valid and inside and r['name']): continue
 meta=r['meta']; search=f"{r['name']} {r['description'] or ''} {meta.get('address','')}"; city_ar,city_en,region_ar,region_en,region_code=city_region(search,coords); serials[region_code]+=1; fid=f'LY-ACC-RES-{region_code}-{serials[region_code]:05d}'
 code,sub_ar,sub_en,class_score=classify(r['name'],r['description']); image=r['images'][0] if r['images'] else None; provider='google_mymaps' if image and ('googleusercontent' in image or 'mymaps.usercontent.google.com' in image) else ('remote_other' if image else None)
 name_en=meta.get('name_en') or None; phone=meta.get('phone') or None; website=meta.get('website') or None; units=num(meta.get('units')); beds=num(meta.get('beds')); capacity=num(meta.get('capacity'))
 required={'name':r['name'],'coordinates':True,'classification':code!='review_required','municipality':city_ar,'address':meta.get('address'),'contact':phone or website,'rooms':None,'beds':beds,'units':units,'capacity':capacity,'services':meta.get('services'),'license':None,'operation':None,'image':False}
 completeness=round(100*sum(bool(v) for v in required.values())/len(required)); scores={'name_score':1.0,'coordinate_score':1.0,'classification_score':class_score,'contact_score':1.0 if phone or website else 0.0,'capacity_score':1.0 if any((beds,units,capacity)) else 0.0,'services_score':1.0 if meta.get('services') else 0.0,'image_score':0.0}; overall=round(sum(scores.values())/len(scores),2); quality='high' if completeness>=70 else 'medium' if completeness>=45 else 'low'
 p={'id':fid,'name_ar':r['name'],'name_en':name_en,'name_normalized_ar':norm(r['name']),'translation_status':'source_provided' if name_en else 'not_available','category':'القرى والمنتجعات السياحية','subcategory_ar':sub_ar,'subcategory_en':sub_en,'facility_type_code':code,'municipality_ar':city_ar,'municipality_en':city_en,'city_ar':city_ar,'city_en':city_en,'region_ar':region_ar,'region_en':region_en,'address_ar':meta.get('address') or None,'address_en':None,'longitude':coords[0],'latitude':coords[1],'source':'Tourist villages and resorts KML','source_kml':'data/incoming/tourist-villages-resorts.kml','source_record_index':r['index'],'description_ar':r['description'],'description_en':None,'phone':phone,'email':None,'website':website,'stars':None,'rooms':None,'beds':beds,'units':units,'capacity':capacity,'beach_access':None,'pool_available':None,'restaurant_available':None,'parking_available':None,'family_friendly':None,'status':None,'license_status':None,'operational_status':None,'ownership_type':None,'data_quality_status':quality,'data_review_status':'review_required' if code=='review_required' else 'integrated','source_image_url':image,'source_image_provider':provider,'source_image_status':'temporary_google_url' if provider=='google_mymaps' else ('available_remote' if image else 'no_image'),'local_images':[],'image_count':0,'created_at':TODAY,'updated_at':TODAY,**scores,'completeness_score':completeness/100,'overall_quality_score':overall,'data_completeness_percent':completeness,'missing_fields':[k for k,v in required.items() if not v],'match_status':match_by_index.get(r['index'],'new_feature'),'coordinate_review_status':'valid','coordinate_change_reason':None,'original_coordinates':coords[:]}
 features.append({'type':'Feature','id':fid,'properties':p,'geometry':{'type':'Point','coordinates':coords}}); paired.append((r,p))
dupes=[]
for i,a in enumerate(features):
 for b in features[i+1:]:
  pa,pb=a['properties'],b['properties']; d=dist(a['geometry']['coordinates'],b['geometry']['coordinates']); s=sim(pa['name_ar'],pb['name_ar']); cls=None
  if d<1 and s==1:cls='confirmed_duplicate'
  elif d<30 and s==1:cls='confirmed_duplicate'
  elif d<100 and s>=.86:cls='review_required'
  if cls:dupes.append([pa['id'],pa['name_ar'],pb['id'],pb['name_ar'],round(d,1),round(s,3),cls,'retain_and_review','No automatic merge; co-located village and resort may be distinct'])
OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps({'type':'FeatureCollection','name':'Libya tourist villages and resorts','metadata':{'source':'data/incoming/tourist-villages-resorts.kml','generated_at':TODAY,'feature_count':len(features)},'features':features},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inventory=[]
for r in source:
 c=r['coords']; inside=bool(c and 9<=c[0]<=26 and 19<=c[1]<=34); inventory.append([r['index'],r['name'],norm(r['name']),c[0] if c else '',c[1] if c else '','valid_point' if r['geometry']=='Point' and c else 'invalid_or_missing','available' if r['description'] else 'missing',r['images'][0] if r['images'] else '','temporary_google_url' if r['images'] else 'no_image',r['style'],r['folder'],'duplicate_name' if name_counts[norm(r['name'])]>1 else 'unique','duplicate_coordinate' if c and coord_counts[tuple(round(x,7) for x in c)]>1 else 'unique','outside_libya' if c and not inside else match_by_index.get(r['index'],'new_feature')])
write_csv(ROOT/'docs/layers/tourist-villages-resorts-kml-inventory.csv',['source_index','source_name','normalized_name','longitude','latitude','geometry_status','description_status','image_url','image_status','style_url','folder','duplicate_name_status','duplicate_coordinate_status','notes'],inventory)
write_csv(ROOT/'docs/layers/tourist-villages-resorts-final-inventory.csv',['id','name_ar','name_en','facility_type_code','municipality_ar','longitude','latitude','match_status','data_quality_status','data_completeness_percent','source_image_status'],[[p[k] or '' for k in ['id','name_ar','name_en','facility_type_code','municipality_ar','longitude','latitude','match_status','data_quality_status','data_completeness_percent','source_image_status']] for _,p in paired])
write_csv(ROOT/'docs/review/tourist-villages-resorts-duplicate-review.csv',['record_a_id','record_a_name','record_b_id','record_b_name','distance_meters','name_similarity','duplicate_classification','recommended_action','notes'],dupes)
write_csv(ROOT/'docs/review/tourist-villages-resorts-data-quality-review.csv',['id','name_ar','quality_status','completeness_percent','missing_fields','review_status','notes'],[[p['id'],p['name_ar'],p['data_quality_status'],p['data_completeness_percent'],'|'.join(p['missing_fields']),p['data_review_status'],'Complete from tourism authority or municipality; verify classification'] for _,p in paired if p['missing_fields'] or p['data_review_status']=='review_required'])
types=Counter(p['facility_type_code'] for _,p in paired); cities=Counter(p['city_ar'] or 'غير محدد' for _,p in paired); qualities=Counter(p['data_quality_status'] for _,p in paired); confirmed=sum(r[6]=='confirmed_duplicate' for r in dupes); review=sum(r[6]=='review_required' for r in dupes); images=sum(bool(r['images']) for r in source); invalid=sum(not r['coords'] or not(-180<=r['coords'][0]<=180 and -90<=r['coords'][1]<=90) for r in source); outside=sum(bool(r['coords']) and not(9<=r['coords'][0]<=26 and 19<=r['coords'][1]<=34) for r in source)
report=f'''# تقرير دمج طبقة القرى والمنتجعات السياحية\n\n## الملخص\n\n- نقاط المصدر: {len(source)}\n- العدد النهائي: {len(features)}\n- العناصر المطابقة مع الطبقة المنشورة السابقة: {len(matched_old)}\n- العناصر الجديدة: {len(features)-len(matched_old)}\n- التكرارات المؤكدة: {confirmed}\n- حالات التكرار التي تحتاج مراجعة: {review}\n- السجلات ذات روابط الصور: {images}\n\n## توزيع التصنيفات\n\n{chr(10).join(f'- {k}: {v}' for k,v in sorted(types.items()))}\n\n## التوزيع المكاني المتاح\n\n{chr(10).join(f'- {k}: {v}' for k,v in cities.most_common())}\n\n## جودة البيانات\n\n{chr(10).join(f'- {k}: {v}' for k,v in sorted(qualities.items()))}\n\n## الفجوات والجهات المطلوبة\n\nتوجد فجوات في الغرف والأسرة والوحدات والطاقة والخدمات وحالة الترخيص والتشغيل. يلزم استكمالها من وزارة السياحة والبلديات وجهات الترخيص ومشغلي المنشآت. لم تُخترع قيم غير واردة في المصدر، ولم تُنزّل أو تُعرض روابط Google وMy Maps تلقائيًا، ولم تُدمج الحالات غير المؤكدة.\n'''; (ROOT/'docs/tourist-villages-resorts-kml-integration-report.md').write_text(report,encoding='utf-8')
print(f'RESORTS_SOURCE_KML_EXISTS = {SOURCE.exists()}'); print(f'RESORTS_SOURCE_FILE_SIZE = {SOURCE.stat().st_size}'); print(f'RESORTS_SOURCE_PLACEMARKS_TOTAL = {len(source)}'); print(f'RESORTS_TOTAL_PLACEMARKS = {len(source)}'); print(f'RESORTS_WITH_VALID_POINT_GEOMETRY = {sum(r["geometry"]=="Point" and bool(r["coords"]) for r in source)}'); print(f'RESORTS_WITHOUT_COORDINATES = {sum(not r["coords"] for r in source)}'); print(f'RESORTS_WITH_IMAGES = {images}'); print(f'RESORTS_WITHOUT_IMAGES = {len(source)-images}'); print(f'RESORTS_WITH_DESCRIPTIONS = {sum(bool(r["description"]) for r in source)}'); print(f'RESORTS_WITHOUT_DESCRIPTIONS = {sum(not r["description"] for r in source)}'); print(f'RESORTS_DUPLICATE_NAMES = {sum(v-1 for v in name_counts.values() if v>1)}'); print(f'RESORTS_DUPLICATE_COORDINATES = {sum(v-1 for v in coord_counts.values() if v>1)}'); print(f'RESORTS_INVALID_COORDINATES = {invalid}'); print(f'EXISTING_RESORT_FEATURES = {len(old)}'); print(f'MATCHED_EXISTING_RESORTS = {len(matched_old)}'); print(f'NEW_RESORT_FEATURES = {len(features)-len(matched_old)}'); print('PRESERVED_EXISTING_IDS = 0'); print(f'DUPLICATE_IDS = {len(features)-len({f["id"] for f in features})}'); print(f'VALID_RESORT_COORDINATES = {len(features)}'); print(f'OUTSIDE_LIBYA_COORDINATES = {outside}'); print('COORDINATES_SWAPPED = 0'); print('COORDINATES_CHANGED = 0'); print(f'RESORTS_DUPLICATES_CONFIRMED = {confirmed}'); print(f'RESORTS_DUPLICATES_REVIEW_REQUIRED = {review}')
for key in ['tourist_village','tourist_resort','beach_resort','desert_resort','mountain_resort','eco_resort','family_resort','holiday_village','tourist_complex','camping_resort','accommodation_resort_other','review_required']: print(f'{key.upper()}_COUNT = {types[key]}')
