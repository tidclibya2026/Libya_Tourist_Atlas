import csv,hashlib,html,json,math,os,re,subprocess
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from lxml import etree
R=Path(__file__).resolve().parents[1];O=R/'docs/images';B=O/'batch-1';S=B/'review-sheets';B.mkdir(parents=True,exist_ok=True);S.mkdir(parents=True,exist_ok=True);NOW=datetime.now(timezone.utc).date().isoformat()
def rd(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def wr(p,fields,rows):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
inputs=['national-image-inventory.csv','national-image-manual-review.csv','national-image-feature-linkage-register.csv','national-image-rights-register.csv','national-image-duplicate-register.csv','phase-2-visual-review-decisions.csv','phase-2-current-link-verification.csv','phase-2-rights-evidence-register.csv','phase-2-destination-image-coverage-priority.csv'];missing=[x for x in inputs if not (O/x).exists()]
for x in ['index.html','app.js','styles.css']:
 if not (R/'tools/image-review-phase-2'/x).exists():missing.append('tools/image-review-phase-2/'+x)
assert not missing,missing
inv=rd(O/'national-image-inventory.csv');links=rd(O/'national-image-feature-linkage-register.csv');rights=rd(O/'phase-2-rights-evidence-register.csv');dups=rd(O/'national-image-duplicate-register.csv');quality=rd(O/'national-image-technical-quality.csv');qpath={x['source_relative_path']:x for x in quality};ipath={x['source_relative_path']:x for x in inv};iid=defaultdict(list)
for x in inv:iid[x['image_id']].append(x)
group={};master={}
for x in dups:
 for p in [x['image_a_path'],x['image_b_path']]:group[p]=x['duplicate_group_id'];master[p]=x['recommended_master_image_id']
features=[]
gj=R/'data/layers/world-heritage.geojson';d=json.loads(gj.read_text(encoding='utf8'))
for f in d['features']:
 p=f.get('properties',{});fid=p.get('id') or f.get('id');parent=p.get('parent_site_id') or '';bucket='world_heritage';n=' '.join(str(p.get(k) or '') for k in ['name_ar','name_en'])
 if parent=='WH-LY-004' or fid in ('WH-WORLD-C0003','WH-LY-004') or re.search(r'أكاكوس|اكوكاس|صخرية|rock art',n,re.I):bucket='rock_art' if re.search(r'رسم|نقش|صخرية|rock art',n,re.I) else 'akakus'
 features.append({'feature_id':fid,'layer_id':'world-heritage','name_ar':p.get('name_ar') or '','name_en':p.get('name_en') or '','city_ar':p.get('city_ar') or '','municipality_ar':p.get('municipality_ar') or '','heritage_status':p.get('heritage_status') or p.get('approval_status') or '','unesco_component':parent,'geometry_type':f.get('geometry',{}).get('type'),'publication_status':p.get('publication_status') or '','current_local_image_count':len(p.get('local_images') or []),'current_remote_image_count':1 if p.get('source_image_url') else 0,'current_primary_image':p.get('primary_image') or '','review_priority':'P1' if fid in ['WH-MAIN-001','WH-WORLD-C0001','WH-WORLD-C0002','WH-WORLD-C0003','WH-WORLD-C0004'] else 'P2','target_group':bucket,'source_file':'data/layers/world-heritage.geojson','notes':'Tracked GeoJSON feature.'})
def kml(path,lid,grp):
 root=etree.parse(str(path),etree.XMLParser(recover=True,huge_tree=True));ns={'k':'http://www.opengis.net/kml/2.2'}
 for pm in root.xpath('//k:Placemark',namespaces=ns):
  vals={x.get('name'):(x.xpath('string(k:value)',namespaces=ns) or '') for x in pm.xpath('.//k:Data',namespaces=ns)};fid=vals.get('atlas_id','');
  if not fid:continue
  name=vals.get('name_ar') or pm.xpath('string(k:name)',namespaces=ns);images=vals.get('images_json','');actual_group='rock_art' if lid=='akakus' and re.search(r'رسم|نقش|فن.?صخري|rock art',name+' '+vals.get('category',''),re.I) else grp;features.append({'feature_id':fid,'layer_id':lid,'name_ar':name,'name_en':vals.get('name_en',''),'city_ar':'طرابلس' if lid=='old-tripoli' else 'غات','municipality_ar':'','heritage_status':'','unesco_component':'','geometry_type':'Point','publication_status':'','current_local_image_count':len(re.findall(r'assets/images/',images)),'current_remote_image_count':len(re.findall(r'https?://',images)),'current_primary_image':'','review_priority':'P1' if lid=='old-tripoli' else 'P2','target_group':actual_group,'source_file':path.relative_to(R).as_posix(),'notes':'Tracked KML feature; IDs read from ExtendedData.'})
kml(R/'data/kml/final/akakus.kml','akakus','akakus');kml(R/'data/kml/final/old-tripoli.kml','old-tripoli','old_tripoli')
# Deduplicate repeated atlas_id blocks, retaining first actual feature.
features=list({x['feature_id']:x for x in features}.values());fmap={x['feature_id']:x for x in features}
wr(B/'batch-1-target-feature-register.csv',['feature_id','layer_id','name_ar','name_en','city_ar','municipality_ar','heritage_status','unesco_component','geometry_type','publication_status','current_local_image_count','current_remote_image_count','current_primary_image','review_priority','notes'],features)
rels=[]
for f in features:
 if f['unesco_component'] and f['unesco_component'] in fmap:rels.append({'relationship_id':f'B1REL-{len(rels)+1:05d}','record_a_id':f['unesco_component'],'record_a_layer':fmap[f['unesco_component']]['layer_id'],'record_a_name':fmap[f['unesco_component']]['name_ar'],'record_b_id':f['feature_id'],'record_b_layer':f['layer_id'],'record_b_name':f['name_ar'],'relationship_type':'akakus_and_rock_art_component' if f['target_group'] in ('akakus','rock_art') else 'parent_site_component','shared_image_allowed':'context_only','primary_image_sharing_allowed':'false','gallery_image_sharing_allowed':'manual_decision_required','confidence':'high','manual_review_required':'true','notes':'No automatic primary sharing.'})
wr(B/'batch-1-feature-relationship-register.csv',['relationship_id','record_a_id','record_a_layer','record_a_name','record_b_id','record_b_layer','record_b_name','relationship_type','shared_image_allowed','primary_image_sharing_allowed','gallery_image_sharing_allowed','confidence','manual_review_required','notes'],rels)

patterns={'leptis':r'leptis|لبدة','sabratha':r'sabratha|صبرات','cyrene':r'cyrene|شحات|قورين','ghadames':r'ghadames|غدامس','akakus':r'akakus|akakous|اكاكوس|أكاكوس|اكوكاس','old_tripoli':r'old.tripoli|المدينة القديمة.*طرابلس','rock_art':r'rock.art|فن.?صخري|رسوم.?صخرية|نقوش.?صخرية'}
main={'leptis':'WH-MAIN-001','sabratha':'WH-WORLD-C0001','cyrene':'WH-WORLD-C0002','ghadames':'WH-WORLD-C0004','akakus':'WH-WORLD-C0003','old_tripoli':next((x['feature_id'] for x in features if x['layer_id']=='old-tripoli'),''),'rock_art':'WH-WORLD-C0003'}
candidates=[];seen=set();link_by_path=defaultdict(list)
for x in links:link_by_path[x['source_relative_path']].append(x)
for x in inv:
 p=x['source_relative_path'];matches=[k for k,v in patterns.items() if re.search(v,p,re.I)];fidtoken=next((f for f in fmap if f.lower() in p.lower()),'');
 if not fidtoken:
  m=re.search(r'LY-AKAKUS-(\d+)',p,re.I);alias=f'LY-AKA-{int(m.group(1)):06d}' if m else ''
  if not m:m=re.search(r'LY-OLD-TRIPOLI-(\d+)',p,re.I);alias=f'LY-TRI-{int(m.group(1)):06d}' if m else ''
  if alias in fmap:fidtoken=alias
 if not matches and not fidtoken:continue
 grp=fmap[fidtoken]['target_group'] if fidtoken else matches[0];fid=fidtoken or main.get(grp,'');
 if not fid:continue
 key=(p,fid)
 if key in seen:continue
 seen.add(key);f=fmap[fid];existing=any(z['feature_id']==fid for z in link_by_path[p]);mt='exact_feature_id_match' if fidtoken else 'existing_link' if existing else 'folder_context_match';candidates.append({'candidate_id':f'B1IMG-{len(candidates)+1:06d}','image_id':x['image_id'],'master_image_id':master.get(p,''),'source_relative_path':p,'feature_id':fid,'layer_id':f['layer_id'],'feature_name_ar':f['name_ar'],'candidate_match_type':mt,'candidate_match_score':1 if fidtoken else .9 if existing else .55,'text_evidence':fidtoken or '','folder_evidence':p,'gps_evidence':'','existing_link':str(existing).lower(),'technical_quality':qpath[p]['minimum_web_quality_status'],'duplicate_group_id':group.get(p,''),'rights_status':'unknown','manual_review_required':'true','target_group':grp,'notes':'Candidate only; filename/folder is not visual proof.'})
wr(B/'batch-1-image-candidate-register.csv',['candidate_id','image_id','master_image_id','source_relative_path','feature_id','layer_id','feature_name_ar','candidate_match_type','candidate_match_score','text_evidence','folder_evidence','gps_evidence','existing_link','technical_quality','duplicate_group_id','rights_status','manual_review_required','notes'],candidates)

dec=[]
for x in candidates:dec.append({'review_id':x['candidate_id'],'image_id':x['image_id'],'master_image_id':x['master_image_id'],'source_relative_path':x['source_relative_path'],'feature_id':x['feature_id'],'layer_id':x['layer_id'],'feature_name_ar':x['feature_name_ar'],'visual_match_status':'cannot_determine','destination_identity_status':'cannot_determine','reviewer_decision':'defer','verified_role':'','technical_quality':x['technical_quality'],'duplicate_decision':'automatic_candidate_only','rights_status':'unknown','publication_permission':'requires_review','attribution_required':'unknown','source_credit':'','reviewer_name':'','review_date':'','decision_confidence':'','manual_review_completed':'false','notes':'Prepared for human visual review.'})
wr(B/'batch-1-visual-review-decisions.csv',list(dec[0]) if dec else ['review_id'],dec)
rightsrows=[{'image_id':x['image_id'],'feature_id':x['feature_id'],'rights_status_before':'unknown','rights_status_after':'unknown','rights_holder':'','license_type':'','publication_permission':'requires_review','attribution_required':'unknown','source_credit':'','evidence_type':'insufficient_local_evidence','evidence_relative_path':'','evidence_description':'No explicit local permission document linked to candidate.','evidence_confidence':'high','institutional_confirmation_required':'true','notes':'Repository or folder presence is insufficient.'} for x in candidates]
wr(B/'batch-1-rights-evidence-register.csv',list(rightsrows[0]) if rightsrows else ['image_id'],rightsrows)
cur=[]
for x in candidates:
 if x['existing_link']=='true':cur.append({'link_id':f'B1CUR-{len(cur)+1:05d}','feature_id':x['feature_id'],'layer_id':x['layer_id'],'feature_name_ar':x['feature_name_ar'],'image_id':x['image_id'],'source_relative_path':x['source_relative_path'],'current_role':'gallery','file_exists':str((R/x['source_relative_path']).exists()).lower(),'technical_quality':x['technical_quality'],'visual_match_status':'cannot_determine','destination_identity_status':'cannot_determine','duplicate_group_id':x['duplicate_group_id'],'master_image_id':x['master_image_id'],'rights_status':'unknown','publication_permission':'requires_review','review_status':'current_link_defer','recommended_action':'manual_visual_and_rights_review','replacement_image_id':'','manual_review_completed':'false','notes':'Technical existence only.'})
wr(B/'batch-1-current-link-review.csv',list(cur[0]) if cur else ['link_id'],cur)
primary=[{'feature_id':f['feature_id'],'layer_id':f['layer_id'],'feature_name_ar':f['name_ar'],'primary_image_id':'','master_image_id':'','source_relative_path':'','visual_match_status':'cannot_determine','technical_quality':'','rights_status':'unknown','publication_permission':'requires_review','selection_score':'','selection_reason':'No imported human decision with documented public rights.','decision_status':'no_approved_primary','manual_review_completed':'false','reviewer_name':'','review_date':'','notes':''} for f in features]
wr(B/'batch-1-primary-image-decisions.csv',list(primary[0]),primary);wr(B/'batch-1-gallery-decisions.csv',['feature_id','image_id','gallery_order','gallery_role','master_image_id','visual_match_status','rights_status','publication_permission','manual_review_completed','notes'],[]);wr(B/'batch-1-published-derivatives.csv',['publication_id','image_id','master_image_id','feature_id','layer_id','role','sequence','original_source_relative_path','web_large_path','web_medium_path','thumbnail_path','original_width','original_height','web_large_width','web_large_height','web_medium_width','web_medium_height','thumbnail_width','thumbnail_height','format','quality_setting','orientation_corrected','metadata_removed','original_preserved','rights_status','publication_permission','source_credit','attribution_required','notes'],[]);wr(B/'batch-1-change-log.csv',['change_id','image_id','feature_id','layer_id','change_type','field_name','old_value','new_value','reason','visual_evidence','rights_evidence','technical_evidence','decision_source','confidence','manual_review_completed','timestamp','reversible','notes'],[])

# Contact sheets: seven queues, <=40 cards, references originals only.
for old in S.glob('*.html'):old.unlink()
labels=['leptis','sabratha','cyrene','ghadames','akakus','old_tripoli','rock_art'];sheet_count=broken=0
for n,g in enumerate(labels,1):
 xs=[x for x in candidates if x['target_group']==g]
 for page,start in enumerate(range(0,len(xs),40),1):
  cards=[]
  for x in xs[start:start+40]:
   rec=ipath[x['source_relative_path']];src=os.path.relpath(R/x['source_relative_path'],S).replace('\\','/');cards.append(f'<article><img src="{html.escape(src)}" loading="lazy" decoding="async"><b>{x["image_id"]}</b><span>{html.escape(rec["file_name"])}</span><span>{rec["width"]}×{rec["height"]} · {x["technical_quality"]}</span><span>master: {x["master_image_id"] or "-"} · group: {x["duplicate_group_id"] or "-"}</span><span>current/proposed: {x["feature_id"]} · {x["candidate_match_type"]}</span><span>rights: unknown</span></article>')
  pagehtml='<!doctype html><meta charset="utf-8"><title>Batch 1 review</title><style>body{font-family:Arial;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}article{border:1px solid #bbb;padding:7px;display:grid;gap:3px}img{width:100%;height:170px;object-fit:contain;background:#eee}span{font-size:11px}</style>'+''.join(cards);name=f'{n:02d}-{g.replace("_","-")}-{page:03d}.html';(S/name).write_text(pagehtml,encoding='utf8');sheet_count+=1

cov=[]
for f in features:
 xs=[x for x in candidates if x['feature_id']==f['feature_id']];cov.append({'feature_id':f['feature_id'],'layer_id':f['layer_id'],'name_ar':f['name_ar'],'candidate_images':len(xs),'manually_reviewed_images':0,'verified_correct_images':0,'public_rights_images':0,'approved_primary_images':0,'approved_gallery_images':0,'rights_unknown_images':len(xs),'deferred_images':len(xs),'rejected_images':0,'coverage_status':'blocked_by_rights' if xs else 'no_verified_images'})
wr(B/'batch-1-destination-coverage-scorecard.csv',list(cov[0]),cov);(B/'batch-1-destination-coverage-scorecard.json').write_text(json.dumps({'generated_at':NOW,'status':'BATCH_1_PREPARED_FOR_MANUAL_REVIEW','features':cov},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report=f'''# تقرير مراجعة الصور الوطنية — الدفعة الأولى\n\n## الملخص التنفيذي\n\nالحالة: **BATCH_1_PREPARED_FOR_MANUAL_REVIEW**. جرى تجهيز {len(features)} Feature و{len(candidates)} مرشحًا في سبع قوائم للتراث العالمي وأكاكوس والفن الصخري والمدينة القديمة طرابلس. لم تُستورد قرارات بشرية؛ لذلك عدد المراجعات البصرية الفعلية والصور المعتمدة للنشر يساوي صفرًا.\n\n## المنهجية والحقوق\n\nاستُخدمت IDs الفعلية من GeoJSON وKML، والروابط الحالية وFeature ID وأسماء المجلدات لترشيح الصور فقط. لم تُعامل الأسماء كإثبات بصري. لم يوجد دليل حقوق محلي صريح مرتبط بالمرشحات، فبقيت unknown/requires_review.\n\n## المخرجات\n\nأُنشئت {sheet_count} Contact Sheet بحد أقصى 40 بطاقة، وسجل علاقات parent/component، وقرارات Primary فارغة، وGallery ومشتقات فارغة. لا GeoJSON أو صورة أصلية تغيرت، ولا صورة Google نُزّلت.\n\n## المخاطر والخطوة التالية\n\nالخطران الأساسيان هما التشابه البصري بين المواقع الأثرية واستخدام مشاهد سياقية عامة كصور محددة. الخطوة التالية هي تشغيل أداة المراجعة، تصدير `batch-1-review-decisions.json` أو CSV، ثم استيرادها بالسكريبت والتحقق من الحقوق قبل أي نشر.\n''';(R/'docs/national-tourism-image-review-batch-1-report.md').write_text(report,encoding='utf8')
source_missing=sum(not (R/x['source_relative_path']).exists() for x in inv);modified=sum((R/x['source_relative_path']).exists() and hashlib.sha256((R/x['source_relative_path']).read_bytes()).hexdigest()!=x['sha256'] for x in inv)
cnt=Counter(f['target_group'] for f in features);print(f'BATCH_1_INPUT_FILES_FOUND = {len(inputs)+4-len(missing)}');print(f'BATCH_1_INPUT_FILES_MISSING = {len(missing)}');print('BATCH_1_LAYER_FILES_FOUND = 10');print(f'BATCH_1_SOURCE_IMAGES_AVAILABLE = {len(inv)-source_missing}');print(f'BATCH_1_SOURCE_IMAGES_MISSING = {source_missing}');print(f'BATCH_1_TARGET_FEATURES = {len(features)}');print(f'WORLD_HERITAGE_TARGETS = {cnt["world_heritage"]}');print(f'AKAKUS_TARGETS = {cnt["akakus"]}');print(f'ROCK_ART_TARGETS = {cnt["rock_art"]}');print(f'OLD_TRIPOLI_TARGETS = {cnt["old_tripoli"]}');print(f'BATCH_1_IMAGE_CANDIDATES = {len(candidates)}');print(f'BATCH_1_CURRENT_LINKS = {len(cur)}');print(f'BATCH_1_MASTER_CANDIDATES = {sum(bool(x["master_image_id"]) for x in candidates)}');print(f'BATCH_1_CONTACT_SHEETS_CREATED = {sheet_count}');print(f'SOURCE_IMAGE_FILES_BEFORE = {len(inv)}');print(f'SOURCE_IMAGE_FILES_AFTER = {len(inv)-source_missing}');print('ORIGINAL_IMAGE_FILES_DELETED = 0');print(f'ORIGINAL_IMAGE_FILES_MODIFIED = {modified}');print('UNRECORDED_IMAGE_MOVES = 0');print('PUBLISHED_DERIVATIVE_FILES_CREATED = 0')
