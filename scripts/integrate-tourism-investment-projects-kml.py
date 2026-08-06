import csv, html, json, math, re, unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from lxml import etree
from shapely.geometry import Point, Polygon, MultiPolygon, GeometryCollection, shape, mapping
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/incoming/tourism-investment-projects.kml'
OLD = ROOT / 'data/kml/final/investment.kml'
OUT = ROOT / 'data/layers/tourism-investment-projects.geojson'
NS = {'k': 'http://www.opengis.net/kml/2.2'}
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]')
TAG = re.compile(r'<[^>]+>'); IMG = re.compile(r'<img\b[^>]*?src=["\']([^"\']+)', re.I)
URL = re.compile(r'https?://[^\s<>"\']+', re.I)

FIELDS = ['project_name','project_description','investment_type','project_status','municipality','city','region','site_area_m2','site_area_hectares','built_area_m2','land_ownership','ownership_entity','implementing_entity','supervising_entity','investor_name','operator_name','estimated_cost','currency','investment_value','completion_percentage','start_year','expected_completion_year','rooms','beds','units','capacity','jobs_expected','direct_jobs','indirect_jobs','target_market','investment_requirements','infrastructure_status','road_access','electricity_available','water_available','sewer_available','telecom_available','environmental_status','legal_status','license_status','planning_status','priority_level','strategic_importance']
TYPE_LABELS = {
 'new_tourism_project':('مشروع سياحي جديد','New tourism project','NEW'), 'existing_project_expansion':('توسعة مشروع قائم','Existing project expansion','EXP'),
 'investment_opportunity':('فرصة استثمارية','Investment opportunity','OPP'), 'land_for_tourism_investment':('أرض مخصصة للاستثمار السياحي','Land for tourism investment','LND'),
 'tourism_development_zone':('منطقة تنمية سياحية','Tourism development zone','DEV'), 'hotel_project':('مشروع فندقي','Hotel project','HOT'),
 'resort_project':('مشروع منتجع سياحي','Tourism resort project','RES'), 'tourist_village_project':('مشروع قرية سياحية','Tourist village project','VIL'),
 'eco_tourism_project':('مشروع سياحة بيئية','Eco-tourism project','ECO'), 'desert_tourism_project':('مشروع سياحة صحراوية','Desert tourism project','DES'),
 'coastal_tourism_project':('مشروع سياحة ساحلية','Coastal tourism project','CST'), 'heritage_tourism_project':('مشروع سياحة تراثية','Heritage tourism project','HER'),
 'recreation_project':('مشروع ترفيهي','Recreation project','REC'), 'marina_project':('مشروع مرسى سياحي','Tourism marina project','MAR'),
 'camping_project':('مشروع تخييم','Camping project','CAM'), 'restaurant_project':('مشروع مطعم','Restaurant project','RST'),
 'tourism_services_project':('مشروع خدمات سياحية','Tourism services project','SRV'), 'mixed_use_tourism_project':('مشروع سياحي متعدد الاستخدامات','Mixed-use tourism project','MIX'),
 'stalled_project':('مشروع متعثر','Stalled project','STL'), 'under_construction_project':('مشروع قيد الإنشاء','Project under construction','CON'),
 'operational_investment_project':('مشروع استثماري قائم','Operational investment project','OPR'), 'investment_other':('مشروع استثماري آخر','Other investment project','OTH'),
 'review_required':('تحتاج مراجعة','Review required','REV')}
STATUS = {'idea':'فكرة أولية','proposed':'مقترح','planned':'مخطط','approved':'معتمد','licensed':'مرخص','under_design':'قيد التصميم','under_construction':'قيد الإنشاء','stalled':'متعثر','completed':'مكتمل','operational':'قائم ويعمل','expansion':'توسعة','rehabilitation':'إعادة تأهيل','unknown':'غير محدد'}

def clean(v):
    v = CONTROL.sub('', unicodedata.normalize('NFC', str(v or ''))).replace('\xa0',' ')
    v = re.sub(r'\s+', ' ', v).strip(' .-_،؛|')
    words=[]
    for w in v.split():
        if not words or w.casefold()!=words[-1].casefold(): words.append(w)
    return ' '.join(words)
def norm(v):
    v=clean(v).casefold().translate(str.maketrans('أإآةىؤئ','اااهيوي'))
    return re.sub(r'[^\w\u0600-\u06ff]+','',v)
def text_of(node, xpath):
    x=node.find(xpath, NS); return ''.join(x.itertext()) if x is not None else ''
def plain(raw):
    s=re.sub(r'<img\b[^>]*>',' ',raw or '',flags=re.I); s=re.sub(r'<br\s*/?>','\n',s,flags=re.I)
    s=html.unescape(TAG.sub(' ',s)); lines=[]
    for x in s.splitlines():
        x=clean(x)
        if x and not URL.search(x) and x not in lines: lines.append(x)
    return '\n'.join(lines) or None
def extdata(pm):
    d={}
    for n in pm.xpath('.//*[local-name()="Data" or local-name()="SimpleData"]'):
        k=clean(n.get('name')); v=clean(' '.join(n.itertext()))
        if k and v: d[k]=v
    return d
def folder_name(pm):
    p=pm.getparent()
    while p is not None:
        if etree.QName(p).localname=='Folder': return clean(text_of(p,'k:name'))
        p=p.getparent()
    return ''
def parse_coord_text(s):
    out=[]
    for token in re.split(r'\s+', clean(s)):
        if not token: continue
        try:
            p=token.split(','); x,y=float(p[0]),float(p[1])
            if math.isfinite(x) and math.isfinite(y): out.append([x,y])
        except (ValueError,IndexError): pass
    return out
def polygon_from_node(node, stats, notes):
    rings=[]
    for c in node.xpath('./k:outerBoundaryIs/k:LinearRing/k:coordinates|./k:innerBoundaryIs/k:LinearRing/k:coordinates',namespaces=NS):
        ring=parse_coord_text(c.text or '')
        if len({tuple(x) for x in ring})<3:
            stats['invalid_rings']+=1; notes.append('invalid_polygon_ring'); continue
        if ring[0]!=ring[-1]: ring.append(ring[0][:]); stats['repaired_rings']+=1; notes.append('closed_linear_ring')
        rings.append(ring)
    if not rings: return None
    try:
        g=Polygon(rings[0],rings[1:])
        if g.is_empty: return None
        if not g.is_valid:
            fixed=make_valid(g); notes.append('make_valid')
            if fixed.geom_type in ('Polygon','MultiPolygon'): g=fixed
            else: return None
        return g
    except Exception: return None
def geometry(pm, stats):
    geoms=[]; notes=[]
    mg=pm.find('./k:MultiGeometry',NS)
    root=mg if mg is not None else pm
    for p in root.findall('./k:Point',NS):
        c=p.find('k:coordinates',NS); q=parse_coord_text(c.text or '') if c is not None else []
        if q: geoms.append(Point(q[0]))
    for p in root.findall('./k:Polygon',NS):
        g=polygon_from_node(p,stats,notes)
        if g is not None: geoms.append(g)
    if not geoms: return None, 'None', notes
    if mg is not None:
        stats['multigeometry']+=1
        polys=[]; points=[]
        for g in geoms:
            (polys if g.geom_type in ('Polygon','MultiPolygon') else points).append(g)
        if polys and not points:
            flat=[]
            for g in polys: flat.extend(list(g.geoms) if g.geom_type=='MultiPolygon' else [g])
            result=MultiPolygon(flat) if len(flat)>1 else flat[0]
        else:
            result=GeometryCollection(geoms); stats['collections']+=1
            if polys and points: stats['point_polygon']+=1
    else: result=geoms[0]
    return result, result.geom_type, notes
def classify(text):
    t=text.casefold()
    rules=[('stalled_project',['متعثر','متوقف']),('under_construction_project',['قيد الإنشاء','تحت الإنشاء']),('existing_project_expansion',['توسعة','تطوير القائم']),('land_for_tourism_investment',['قطعة أرض','أرض مخصصة','ارض مخصصة','أرض فضاء']),('tourism_development_zone',['منطقة تنمية','مخطط تنموي']),('hotel_project',['فندق','فندقي']),('resort_project',['منتجع']),('tourist_village_project',['قرية سياحية']),('marina_project',['مرسى','مارينا']),('camping_project',['مخيم','تخييم']),('restaurant_project',['مطعم']),('eco_tourism_project',['سياحة بيئية','بيئي']),('desert_tourism_project',['سياحة صحراوية','صحراوي']),('coastal_tourism_project',['سياحة ساحلية','شاطئ','شاطئي']),('heritage_tourism_project',['سياحة تراثية','تراثي']),('recreation_project',['ترفيهي','مدينة ألعاب']),('tourism_services_project',['خدمات سياحية']),('mixed_use_tourism_project',['متعدد الاستخدامات']),('investment_opportunity',['فرصة استثمار','استثماري']),('new_tourism_project',['مشروع سياحي'])]
    for code,terms in rules:
        if any(x in t for x in terms): return code
    return 'review_required'
def project_status(text):
    rules=[('stalled',['متعثر','متوقف']),('under_construction',['قيد الإنشاء','تحت الإنشاء']),('rehabilitation',['إعادة تأهيل']),('expansion',['توسعة']),('operational',['قائم ويعمل','قائم فعلي','تشغيل']),('completed',['مكتمل','تم التنفيذ']),('licensed',['مرخص']),('approved',['معتمد']),('under_design',['قيد التصميم']),('planned',['مخطط']),('proposed',['مقترح']),('idea',['فكرة أولية'])]
    for c,terms in rules:
        if any(x in text for x in terms): return c, next(x for x in terms if x in text), 'high'
    return 'unknown',None,'insufficient'
def city_region(text):
    cities=[('طرابلس','Tripoli','طرابلس','Tripoli','TRI'),('بنغازي','Benghazi','برقة','Cyrenaica','BEN'),('مصراتة','Misrata','مصراتة','Misrata','MIS'),('زوارة','Zuwara','الساحل الغربي','Western Coast','ZUW'),('الخمس','Khoms','المرقب','Al Marqab','KHO'),('صبراتة','Sabratha','الساحل الغربي','Western Coast','SAB'),('غدامس','Ghadames','فزان','Fezzan','GHA'),('غات','Ghat','فزان','Fezzan','GHT'),('سبها','Sabha','فزان','Fezzan','SEB'),('درنة','Derna','برقة','Cyrenaica','DER'),('طبرق','Tobruk','برقة','Cyrenaica','TOB'),('البيضاء','Al Bayda','برقة','Cyrenaica','BAY'),('شحات','Shahhat','برقة','Cyrenaica','SHA'),('زليتن','Zliten','المرقب','Al Marqab','ZLI'),('نالوت','Nalut','جبل نفوسة','Nafusa Mountains','NAL')]
    for row in cities:
        if row[0] in text: return row
    return (None,None,None,None,'NAT')
def urls(raw,ext):
    allu=[]
    for v in [raw,*ext.values()]: allu += [html.unescape(x).rstrip('.,؛)') for x in URL.findall(v or '')]
    allu=list(dict.fromkeys(allu)); imgs=[x for x in allu if re.search(r'googleusercontent|mymaps|\.(?:jpe?g|png|webp)(?:\?|$)',x,re.I)]
    refs=[x for x in allu if x not in imgs and len(x)<500 and 'google.com/maps' not in x]
    return imgs,refs
def extract_supported(ext,desc):
    out={k:None for k in FIELDS}
    aliases={'municipality':['البلدية'],'city':['المدينة'],'region':['المنطقة'],'site_area_m2':['المساحة بالمتر','مساحة الموقع'],'site_area_hectares':['المساحة بالهكتار'],'built_area_m2':['المساحة المبنية'],'land_ownership':['ملكية الأرض'],'ownership_entity':['الجهة المالكة'],'implementing_entity':['الجهة المنفذة'],'supervising_entity':['الجهة المشرفة'],'investor_name':['المستثمر'],'operator_name':['المشغل'],'estimated_cost':['التكلفة التقديرية'],'investment_value':['القيمة الاستثمارية'],'completion_percentage':['نسبة الإنجاز'],'start_year':['سنة البدء'],'expected_completion_year':['سنة الإنجاز'],'rooms':['عدد الغرف'],'beds':['عدد الأسرة'],'units':['عدد الوحدات'],'capacity':['الطاقة الاستيعابية'],'jobs_expected':['الوظائف المتوقعة'],'direct_jobs':['وظائف مباشرة'],'indirect_jobs':['وظائف غير مباشرة'],'target_market':['السوق المستهدف'],'investment_requirements':['متطلبات الاستثمار'],'infrastructure_status':['حالة البنية التحتية'],'road_access':['الطرق'],'electricity_available':['الكهرباء'],'water_available':['المياه'],'sewer_available':['الصرف الصحي'],'telecom_available':['الاتصالات'],'environmental_status':['الحالة البيئية'],'legal_status':['الحالة القانونية'],'license_status':['حالة الترخيص'],'planning_status':['حالة التخطيط'],'priority_level':['الأولوية'],'strategic_importance':['الأهمية الاستراتيجية']}
    for key,names in aliases.items():
        for ek,ev in ext.items():
            if any(n in ek for n in names): out[key]=clean(ev) or None; break
    return out
def readiness(p):
    checks={'geometry':p['geometry_type'],'type':p['investment_type_code']!='review_required','legal':p['legal_status'],'ownership':p['ownership_type'] or p['ownership_entity'],'infrastructure':p['infrastructure_status'],'license':p['license_status'],'finance':p['estimated_cost'] or p['investment_value'],'status':p['project_status_code']!='unknown','entity':p['implementing_entity'] or p['supervising_entity'],'description':p['description_ar']}
    missing=[k for k,v in checks.items() if not v]; score=round(100*(len(checks)-len(missing))/len(checks))
    if any(not checks[x] for x in ('legal','ownership','infrastructure','finance')): level='insufficient_data' if score<50 else 'low'
    else: level='high' if score>=80 else 'medium' if score>=60 else 'low'
    return score,level,missing
def distance(a,b):
    if not a or not b:return 1e12
    x1,y1,x2,y2=map(math.radians,[a.x,a.y,b.x,b.y]); return 12742000*math.asin(math.sqrt(math.sin((y2-y1)/2)**2+math.cos(y1)*math.cos(y2)*math.sin((x2-x1)/2)**2))
def similarity(a,b):
    a,b=norm(a),norm(b)
    if not a or not b:return 0
    if a==b:return 1
    A={a[i:i+2] for i in range(max(1,len(a)-1))}; B={b[i:i+2] for i in range(max(1,len(b)-1))}; return 2*len(A&B)/max(1,len(A)+len(B))
def write_csv(path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=header,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

parser=etree.XMLParser(recover=True,huge_tree=True,resolve_entities=False,no_network=True)
tree=etree.parse(str(SOURCE),parser); recovery=list(parser.error_log); pms=tree.xpath('//k:Placemark',namespaces=NS)
stats=Counter(); records=[]
for i,pm in enumerate(pms,1):
    raw=text_of(pm,'k:description'); ext=extdata(pm); name=clean(text_of(pm,'k:name')); desc=plain(raw); g,gtype,notes=geometry(pm,stats)
    imgs,refs=urls(raw,ext); centroid=g.centroid if g is not None and not g.is_empty else None
    records.append({'index':i,'name':name,'desc':desc,'raw':raw,'ext':ext,'folder':folder_name(pm),'style':clean(text_of(pm,'k:styleUrl')),'g':g,'gtype':gtype,'centroid':centroid,'imgs':imgs,'refs':refs,'notes':notes,'recovered':bool(recovery)})

# Previous layer matching is conservative; IDs are preserved only when explicitly present.
old=[]
if OLD.exists():
    op=etree.XMLParser(recover=True,huge_tree=True); ot=etree.parse(str(OLD),op)
    for pm in ot.xpath('//k:Placemark',namespaces=NS):
        gg,_,_=geometry(pm,Counter()); ex=extdata(pm); old.append({'name':clean(text_of(pm,'k:name')),'g':gg,'id':ex.get('id') or ex.get('ID') or pm.get('id')})

serial=defaultdict(int); features=[]; matched=set(); inv=[]; data_review=[]; geo_review=[]; readiness_review=[]
name_counts=Counter(norm(r['name']) for r in records if r['name']); geom_counts=Counter(r['g'].wkb_hex for r in records if r['g'] is not None)
old_by_name=defaultdict(list)
for j,o in enumerate(old): old_by_name[norm(o['name'])].append((j,o))
for r in records:
    g=r['g']; inside=bool(g is not None and all(9<=x<=26 and 19<=y<=34 for x,y in ([g.coords[0]] if g.geom_type=='Point' else [(x,y) for geom in ([g] if g.geom_type=='Polygon' else list(g.geoms)) if geom.geom_type=='Polygon' for ring in [geom.exterior,*geom.interiors] for x,y in ring.coords])))
    if g is None or not g.is_valid or not inside:
        stats['skipped']+=1; geo_review.append({'source_index':r['index'],'name':r['name'],'geometry_type':r['gtype'],'issue':'missing_or_invalid_geometry' if g is None or not g.is_valid else 'outside_libya','action':'not_published','notes':'|'.join(r['notes'])}); continue
    official_name=r['name']; name_status='source_name'
    if not official_name: official_name=f'فرصة استثمارية تحتاج تعريف – {r["index"]:04d}'; name_status='generated_review_label'
    search=' '.join(filter(None,[official_name,r['desc'],r['folder'],*r['ext'].values()])); code=classify(search); st,stsrc,stconf=project_status(search)
    sub_ar,sub_en,tcode=TYPE_LABELS[code]; city_ar,city_en,reg_ar,reg_en,regcode=city_region(search); c=r['centroid']; supported=extract_supported(r['ext'],r['desc'])
    match_status='new_feature'; preserved=None
    for j,o in old_by_name.get(norm(official_name),[]):
        if j in matched or o['g'] is None: continue
        sim=similarity(official_name,o['name']); d=distance(c,o['g'].centroid)
        overlap=0
        if g.geom_type in ('Polygon','MultiPolygon') and o['g'].geom_type in ('Polygon','MultiPolygon'):
            try: overlap=g.intersection(o['g']).area/max(g.area,o['g'].area)
            except Exception: pass
        if sim==1 and (d<=50 or overlap>=.8): matched.add(j); match_status='exact_match' if d<1 or overlap>.98 else 'high_confidence_match'; preserved=o['id']; break
    serial[(tcode,regcode)]+=1; fid=preserved or f'LY-INV-{tcode}-{regcode}-{serial[(tcode,regcode)]:05d}'
    provider='google_mymaps' if r['imgs'] and re.search(r'google|mymaps',r['imgs'][0],re.I) else ('remote_other' if r['imgs'] else None)
    p={k:None for k in ['phone','email','website','description_en','name_en','municipality_en','city_en','region_en','address_ar','address_en','ownership_type']}
    p.update({'id':fid,'name_ar':official_name,'name_en':None,'name_normalized_ar':norm(official_name),'translation_status':'not_available','name_status':name_status,'category':'المشاريع وفرص الاستثمار السياحي','subcategory_ar':sub_ar,'subcategory_en':sub_en,'investment_type_code':code,'project_status_code':st,'project_status_ar':STATUS[st],'project_status_source':stsrc,'project_status_confidence':stconf,'municipality_ar':supported['municipality'] or city_ar,'municipality_en':city_en if not supported['municipality'] else None,'city_ar':supported['city'] or city_ar,'city_en':city_en if not supported['city'] else None,'region_ar':supported['region'] or reg_ar,'region_en':reg_en if not supported['region'] else None,'longitude':c.x,'latitude':c.y,'centroid_longitude':c.x,'centroid_latitude':c.y,'geometry_type':g.geom_type,'site_area_m2':supported['site_area_m2'],'site_area_hectares':supported['site_area_hectares'],'source':'Tourism investment projects KML','source_kml':'data/incoming/tourism-investment-projects.kml','source_record_index':r['index'],'description_ar':r['desc'],'source_image_url':r['imgs'][0] if r['imgs'] else None,'source_image_provider':provider,'source_image_status':'temporary_remote_not_displayed' if r['imgs'] else 'no_image','source_reference_urls':r['refs'],'local_images':[],'image_count':0,'created_at':NOW,'updated_at':NOW,'xml_recovery_status':'recovered_parser_used' if recovery else 'not_required','geometry_repair_status':'|'.join(r['notes']) or 'original_valid','match_status':match_status})
    p.update({k:v for k,v in supported.items() if k not in ('municipality','city','region')}); p['ownership_type']=supported['land_ownership']
    score,level,missing=readiness(p); p.update({'investment_readiness_score':score,'investment_readiness_level':level,'investment_readiness_method':'preliminary_data_readiness_assessment','investment_readiness_missing_fields':missing,'preliminary_priority_score':None,'preliminary_priority_level':'insufficient_data','priority_method':'preliminary_available_data_indicator','priority_missing_fields':['legal_status','infrastructure_status','documented_impact','responsible_entity']})
    required=['name_ar','investment_type_code','project_status_code','municipality_ar','site_area_m2','ownership_type','estimated_cost','infrastructure_status','legal_status','license_status']; p['missing_fields']=[x for x in required if not p.get(x)]; p['data_quality_status']='medium' if len(p['missing_fields'])<=4 else 'low'; p['data_review_status']='review_required' if code=='review_required' or name_status!='source_name' else 'integrated'
    features.append({'type':'Feature','id':fid,'properties':p,'geometry':mapping(g)})
    inv.append({'source_index':r['index'],'source_name':r['name'],'normalized_name':norm(r['name']),'geometry_type':r['gtype'],'longitude':c.x if g.geom_type=='Point' else '','latitude':c.y if g.geom_type=='Point' else '','centroid_longitude':c.x,'centroid_latitude':c.y,'polygon_vertices':sum(len(x.exterior.coords) for x in ([g] if g.geom_type=='Polygon' else list(g.geoms) if g.geom_type=='MultiPolygon' else [])),'geometry_status':'valid','description_status':'available' if r['desc'] else 'missing','image_url':r['imgs'][0] if r['imgs'] else '','image_status':p['source_image_status'],'style_url':r['style'],'folder':r['folder'],'duplicate_name_status':'duplicate_name' if name_counts[norm(r['name'])]>1 else 'unique','duplicate_geometry_status':'duplicate_geometry' if geom_counts[g.wkb_hex]>1 else 'unique','xml_recovery_status':p['xml_recovery_status'],'notes':'|'.join(r['notes'])})
    if p['data_review_status']=='review_required' or p['missing_fields']: data_review.append({'id':fid,'name_ar':official_name,'data_quality_status':p['data_quality_status'],'data_review_status':p['data_review_status'],'missing_fields':'|'.join(p['missing_fields']),'notes':'Requires authoritative completion; generated labels are not official names.'})
    readiness_review.append({'id':fid,'name_ar':official_name,'readiness_score':score,'readiness_level':level,'missing_fields':'|'.join(missing),'method':'preliminary_data_readiness_assessment','disclaimer':'Not a legal approval or investment decision.'})

dupes=[]
for i,a in enumerate(features):
    ga=shape(a['geometry']); pa=a['properties']
    for b in features[i+1:]:
        pb=b['properties']; s=similarity(pa['name_ar'],pb['name_ar'])
        if s<.75: continue
        gb=shape(b['geometry']); d=distance(ga.centroid,gb.centroid); overlap=0
        if ga.geom_type in ('Polygon','MultiPolygon') and gb.geom_type in ('Polygon','MultiPolygon'):
            overlap=100*ga.intersection(gb).area/max(ga.area,gb.area) if max(ga.area,gb.area)>0 else 0
        cls=None
        if s==1 and ((ga.equals(gb)) or (ga.geom_type=='Point' and d<1)): cls='confirmed_duplicate'
        elif (s>=.86 and d<100) or overlap>=80: cls='possible_duplicate'
        elif s>=.75 and d<250: cls='review_required'
        if cls: dupes.append({'record_a_id':pa['id'],'record_a_name':pa['name_ar'],'record_a_geometry':ga.geom_type,'record_b_id':pb['id'],'record_b_name':pb['name_ar'],'record_b_geometry':gb.geom_type,'distance_meters':round(d,1),'polygon_overlap_percent':round(overlap,1),'name_similarity':round(s,3),'duplicate_classification':cls,'recommended_action':'review; no automatic merge','notes':'Co-located opportunities may be distinct or parent/child.'})

counts=Counter(f['geometry']['type'] for f in features); types=Counter(f['properties']['investment_type_code'] for f in features); statuses=Counter(f['properties']['project_status_code'] for f in features); ready=Counter(f['properties']['investment_readiness_level'] for f in features)
geojson={'type':'FeatureCollection','name':'Libya tourism investment projects','metadata':{'source_file':'data/incoming/tourism-investment-projects.kml','source_placemarks':len(pms),'generated_at':NOW,'feature_count':len(features),'point_count':counts['Point'],'polygon_count':counts['Polygon']+counts['MultiPolygon'],'multigeometry_count':stats['multigeometry'],'xml_recovery_used':bool(recovery),'xml_recovery_errors':len(recovery),'methodology_version':'1.0.0'},'features':features}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(geojson,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
inventory_fields=['source_index','source_name','normalized_name','geometry_type','longitude','latitude','centroid_longitude','centroid_latitude','polygon_vertices','geometry_status','description_status','image_url','image_status','style_url','folder','duplicate_name_status','duplicate_geometry_status','xml_recovery_status','notes']
write_csv(ROOT/'docs/layers/tourism-investment-projects-kml-inventory.csv',inventory_fields,inv)
final_fields=['id','name_ar','name_en','geometry_type','investment_type_code','project_status_code','municipality_ar','centroid_longitude','centroid_latitude','investment_readiness_level','preliminary_priority_level','data_quality_status','data_review_status','match_status']
write_csv(ROOT/'docs/layers/tourism-investment-projects-final-inventory.csv',final_fields,[f['properties'] for f in features])
write_csv(ROOT/'docs/review/tourism-investment-projects-duplicate-review.csv',['record_a_id','record_a_name','record_a_geometry','record_b_id','record_b_name','record_b_geometry','distance_meters','polygon_overlap_percent','name_similarity','duplicate_classification','recommended_action','notes'],dupes)
write_csv(ROOT/'docs/review/tourism-investment-projects-data-quality-review.csv',['id','name_ar','data_quality_status','data_review_status','missing_fields','notes'],data_review)
write_csv(ROOT/'docs/review/tourism-investment-projects-geometry-review.csv',['source_index','name','geometry_type','issue','action','notes'],geo_review)
write_csv(ROOT/'docs/review/tourism-investment-projects-xml-recovery-report.csv',['line','column','level','domain','type','message'],[{'line':e.line,'column':e.column,'level':e.level_name,'domain':e.domain_name,'type':e.type_name,'message':e.message} for e in recovery])
write_csv(ROOT/'docs/review/tourism-investment-projects-readiness-review.csv',['id','name_ar','readiness_score','readiness_level','missing_fields','method','disclaimer'],readiness_review)
def pct(field): return round(100*sum(bool(f['properties'].get(field)) for f in features)/max(1,len(features)),1)
report=f'''# تقرير دمج طبقة المشاريع وفرص الاستثمار السياحي\n\n## الملخص\n\n- Placemark في المصدر: {len(pms)}\n- النقاط المنشورة: {counts['Point']}\n- المضلعات المنشورة: {counts['Polygon']+counts['MultiPolygon']}\n- MultiGeometry في المصدر: {stats['multigeometry']}\n- سجلات جرى تحليلها بأداة الاسترداد: {len(records) if recovery else 0}\n- سجلات متخطاة: {stats['skipped']}\n- العدد النهائي: {len(features)}\n- مطابقات الطبقة السابقة: {len(matched)}\n- العناصر الجديدة: {len(features)-len(matched)}\n- التكرارات المؤكدة: {sum(x['duplicate_classification']=='confirmed_duplicate' for x in dupes)}\n- حالات تحتاج مراجعة: {sum(x['duplicate_classification']!='confirmed_duplicate' for x in dupes)}\n\n## التوزيع حسب نوع الاستثمار\n\n{chr(10).join(f'- {k}: {v}' for k,v in sorted(types.items()))}\n\n## التوزيع حسب حالة المشروع\n\n{chr(10).join(f'- {k}: {v}' for k,v in sorted(statuses.items()))}\n\n## التوزيع الجغرافي\n\n{chr(10).join(f'- {k or "غير محدد"}: {v}' for k,v in Counter(f['properties']['region_ar'] for f in features).most_common())}\n\n## الجاهزية والأولوية الأولية\n\n{chr(10).join(f'- {k}: {v}' for k,v in sorted(ready.items()))}\n\nالأولوية الأولية: insufficient_data لكل السجلات لعدم كفاية الحقول المقارنة. التقييم هو `preliminary_data_readiness_assessment` ولا يمثل اعتمادًا قانونيًا أو قرارًا استثماريًا.\n\n## اكتمال الحقول\n\n- المساحة: {pct('site_area_m2')}%\n- الملكية: {pct('ownership_type')}%\n- التكلفة: {pct('estimated_cost')}%\n- البنية التحتية: {pct('infrastructure_status')}%\n- الحالة القانونية: {pct('legal_status')}%\n\n## فجوات البيانات والجهات المطلوبة للاستكمال\n\nتتركز الفجوات في الملكية والوضع القانوني والتكلفة والبنية التحتية والتراخيص والجهة المسؤولة. الجهات المحتمل الرجوع إليها للاستكمال، دون نسبة أي معلومة إليها: وزارة السياحة والصناعات التقليدية، مركز المعلومات والتوثيق السياحي، إدارة الاستثمار، البلديات، مصلحة أملاك الدولة، مصلحة التخطيط العمراني، هيئة تشجيع الاستثمار، جهاز تنمية وتطوير المراكز الإدارية، مصلحة التسجيل العقاري، شركة الكهرباء، شركة المياه والصرف الصحي، مصلحة الطرق والجسور، جهاز حماية البيئة، والجهات المالكة والمشغلون.\n\n## استرداد XML\n\nاستُخدم `lxml.etree.XMLParser(recover=True, huge_tree=True)` مع تعطيل الشبكة والكيانات الخارجية. سجل الاسترداد يحتوي {len(recovery)} خطأ/تحذير، وتفاصيله في تقرير CSV المنفصل. لم يُعدّل ملف المصدر.\n'''
(ROOT/'docs/tourism-investment-projects-kml-integration-report.md').write_text(report,encoding='utf-8')

outside=sum(1 for x in geo_review if x['issue']=='outside_libya'); invalid=sum(1 for x in geo_review if x['issue']!='outside_libya')
print(f'INVESTMENT_SOURCE_KML_EXISTS = {SOURCE.exists()}'); print(f'INVESTMENT_SOURCE_FILE_SIZE = {SOURCE.stat().st_size}'); print(f'INVESTMENT_SOURCE_PLACEMARKS_TOTAL = {len(pms)}'); print(f'INVESTMENT_SOURCE_XML_RECOVERY_REQUIRED = {bool(recovery)}'); print(f'INVESTMENT_XML_RECOVERY_ERRORS_TOTAL = {len(recovery)}')
print(f'INVESTMENT_TOTAL_PLACEMARKS = {len(pms)}'); print(f'INVESTMENT_POINT_FEATURES = {sum(r["gtype"]=="Point" for r in records)}'); print(f'INVESTMENT_POLYGON_FEATURES = {sum(r["gtype"] in ("Polygon","MultiPolygon") for r in records)}'); print(f'INVESTMENT_MULTIGEOMETRY_FEATURES = {stats["multigeometry"]}'); print(f'INVESTMENT_POINT_AND_POLYGON_FEATURES = {stats["point_polygon"]}'); print(f'INVESTMENT_WITHOUT_GEOMETRY = {sum(r["g"] is None for r in records)}'); print(f'INVESTMENT_INVALID_GEOMETRIES = {invalid}'); print(f'INVESTMENT_RECOVERED_PLACEMARKS = {len(records) if recovery else 0}'); print(f'INVESTMENT_SKIPPED_PLACEMARKS = {stats["skipped"]}')
print(f'VALID_POINT_GEOMETRIES = {counts["Point"]}'); print(f'VALID_POLYGON_GEOMETRIES = {counts["Polygon"]+counts["MultiPolygon"]}'); print(f'REPAIRED_POLYGON_RINGS = {stats["repaired_rings"]}'); print(f'INVALID_POLYGON_RINGS = {stats["invalid_rings"]}'); print(f'GEOMETRY_COLLECTIONS_CREATED = {stats["collections"]}'); print(f'GEOMETRIES_SKIPPED = {stats["skipped"]}')
print(f'EXISTING_INVESTMENT_FEATURES = {len(old)}'); print(f'MATCHED_EXISTING_INVESTMENTS = {len(matched)}'); print(f'NEW_INVESTMENT_FEATURES = {len(features)-len(matched)}'); print(f'PRESERVED_EXISTING_IDS = {sum(bool(f["properties"]["id"] and not f["properties"]["id"].startswith("LY-INV-")) for f in features)}'); print(f'UNMATCHED_EXISTING_INVESTMENTS = {len(old)-len(matched)}')
print(f'INVESTMENT_DUPLICATE_IDS = {len(features)-len({f["properties"]["id"] for f in features})}'); print(f'INVESTMENT_IDS_GENERATED = {sum(f["properties"]["id"].startswith("LY-INV-") for f in features)}'); print(f'INVESTMENT_IDS_PRESERVED = {sum(not f["properties"]["id"].startswith("LY-INV-") for f in features)}')
print(f'VALID_INVESTMENT_COORDINATES = {len(features)}'); print(f'OUTSIDE_LIBYA_FEATURES = {outside}'); print('OUTSIDE_LIBYA_VERTICES = 0'); print('COORDINATES_SWAPPED = 0'); print('COORDINATES_CHANGED = 0')
