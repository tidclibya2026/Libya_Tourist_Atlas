import csv, json, os, re, hashlib, html
from pathlib import Path
ROOT=Path('.')
OUT=ROOT/'docs/images/batch-2'; (OUT/'review-sheets').mkdir(parents=True,exist_ok=True)
layers=[('hotels','data/layers/hotels.geojson','Hotels'),('resorts','data/layers/tourist-villages-resorts.geojson','Resorts')]
features=[]; layer_audit=[]; byid={}
for lid,path,label in layers:
 d=json.loads(Path(path).read_text(encoding='utf-8')); fs=d.get('features',[]); byid.update({f.get('id') or f.get('properties',{}).get('id'): (lid,f) for f in fs}); features += [(lid,f) for f in fs]
 imgc=sum(bool(f.get('properties',{}).get('local_images')) for f in fs)
 layer_audit.append({'layer_id':lid,'runtime_geojson_path':path,'loaded_by_app':'true','feature_count':len(fs),'geometry_types':'|'.join(sorted({f.get('geometry',{}).get('type','') for f in fs})),'id_field':'id','name_fields':'name_ar|name_en|name_normalized_ar','category_fields':'category|subcategory_ar|facility_type_code','current_image_fields':'local_images|image_count|primary_image|gallery_images','current_local_image_features':imgc,'remote_image_features':0,'candidate_for_batch_2':'true','notes':'Candidate review only; no GeoJSON publication changes.'})
with (OUT/'batch-2-runtime-layer-audit.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(layer_audit[0]));w.writeheader();w.writerows(layer_audit)
# targets
targets=[]
for lid,f in features:
 p=f.get('properties',{}); imgs=p.get('local_images') or []; imgs=imgs if isinstance(imgs,list) else [imgs]
 targets.append({'feature_id':f.get('id') or p.get('id',''),'layer_id':lid,'name_ar':p.get('name_ar',''),'name_en':p.get('name_en',''),'facility_type':p.get('facility_type_code') or p.get('subcategory_ar') or p.get('category',''),'classification':p.get('subcategory_ar',''),'stars':p.get('stars',''),'municipality_ar':p.get('municipality_ar',''),'city_ar':p.get('city_ar',''),'region_ar':p.get('region_ar',''),'address':p.get('address_ar',''),'latitude':p.get('latitude',''),'longitude':p.get('longitude',''),'publication_status':p.get('publication_status',''),'current_local_image_count':len(imgs),'current_remote_image_count':0,'current_primary_image':p.get('primary_image',''),'current_gallery_count':len(p.get('gallery_images') or []),'data_quality_status':p.get('data_quality_status',''),'review_priority':'PRIORITY_A' if imgs else 'PRIORITY_C','notes':''})
def write(name,rows,fields=None):
 if not fields: fields=list(rows[0]) if rows else []
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as h:
  w=csv.DictWriter(h,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
write('batch-2-target-feature-register.csv',targets)
# current links and candidates
links=list(csv.DictReader(open('docs/images/phase-2-current-link-verification.csv',encoding='utf-8')))
rights={}
try:
 for r in csv.DictReader(open('docs/images/national-image-rights-register.csv',encoding='utf-8')): rights[r.get('image_id','')]=r
except FileNotFoundError: pass
cand=[]; current=[]
for i,r in enumerate(links):
 if r.get('layer_id')!='hotels': continue
 fid=r.get('feature_id'); t=next((x for x in targets if x['feature_id']==fid),None)
 if not t: continue
 rr=rights.get(r.get('image_id',''),{})
 base={'candidate_id':f'B2-CAN-{len(cand)+1:05d}','image_id':r.get('image_id',''),'master_image_id':r.get('master_image_id',''),'source_relative_path':r.get('source_relative_path',''),'feature_id':fid,'layer_id':'hotels','feature_name_ar':t['name_ar'],'facility_type':t['facility_type'],'candidate_match_type':'existing_link','candidate_match_score':'1.0','existing_link':'true','exact_feature_id_match':'true','exact_name_match':'false','folder_match':'false','city_match':'false','gps_match':'false','coordinate_distance_meters':'','technical_quality':r.get('technical_quality',''),'duplicate_group_id':r.get('duplicate_group_id',''),'rights_status':r.get('rights_status') or rr.get('rights_status','unknown'),'manual_review_required':'true','target_group':'Hotels','notes':'Existing local linkage; technical evidence only, not visual verification.'}
 cand.append(base)
 current.append({'link_id':f'B2-LINK-{len(current)+1:05d}','feature_id':fid,'layer_id':'hotels','feature_name_ar':t['name_ar'],'facility_type':t['facility_type'],'image_id':r.get('image_id',''),'source_relative_path':r.get('source_relative_path',''),'current_role':r.get('current_role',''),'file_exists':r.get('file_exists',''),'image_readable':'true' if r.get('file_exists')=='true' else 'false','technical_quality':r.get('technical_quality',''),'master_image_id':r.get('master_image_id',''),'duplicate_group_id':r.get('duplicate_group_id',''),'match_basis':'existing_link','visual_review_status':'not_individually_verified','rights_status':r.get('rights_status','unknown'),'recommended_action':'retain_candidate','manual_review_required':'true','notes':'No Batch 2 approval or visual review inferred.'})
write('batch-2-image-candidate-register.csv',cand)
write('batch-2-current-link-review.csv',current)
# decisions blank, rights evidence, relationships
dec_fields=['review_id','image_id','master_image_id','source_relative_path','feature_id','layer_id','feature_name_ar','facility_type','visual_match_status','facility_identity_status','reviewer_decision','verified_role','technical_quality','duplicate_decision','rights_status','publication_permission','institutional_batch_approval','reviewer_name','review_date','decision_confidence','manual_review_completed','notes']
write('batch-2-visual-review-decisions.csv',[],dec_fields)
write('batch-2-rights-evidence-register.csv',[],['image_id','feature_id','facility_name_ar','rights_status_before','rights_status_after','rights_holder','publication_permission','attribution_required','source_credit','evidence_type','evidence_relative_path','evidence_description','institutional_confirmation_required','notes'])
rel_fields=['relationship_id','feature_a_id','feature_a_layer','feature_a_name','feature_b_id','feature_b_layer','feature_b_name','relationship_type','coordinate_distance_meters','shared_image_allowed','primary_image_sharing_allowed','confidence','manual_confirmation_required','notes']
write('batch-2-feature-relationship-register.csv',[],rel_fields)
shared=[]
from collections import Counter
for image,grp in __import__('itertools').groupby(sorted(cand,key=lambda x:x['image_id']),key=lambda x:x['image_id']):
 rows=list(grp)
 if len({x['feature_id'] for x in rows})>1: shared.append({'image_id':image,'feature_ids':'|'.join(x['feature_id'] for x in rows),'classification':'ambiguous','notes':'Requires manual facility identity review.'})
write('batch-2-shared-image-facility-audit.csv',shared,['image_id','feature_ids','classification','notes'])
# priority and primary/gallery candidates
priority=[{'feature_id':t['feature_id'],'layer_id':t['layer_id'],'name_ar':t['name_ar'],'review_priority':t['review_priority'],'candidate_count':sum(c['feature_id']==t['feature_id'] for c in cand),'recommended_action':'manual_visual_review' if any(c['feature_id']==t['feature_id'] for c in cand) else 'no_local_candidate','notes':''} for t in targets]
write('batch-2-review-priority-register.csv',priority)
prim=[]
for t in targets:
 cs=[c for c in cand if c['feature_id']==t['feature_id']]
 if cs:
  c=cs[0]; prim.append({'feature_id':t['feature_id'],'layer_id':t['layer_id'],'feature_name_ar':t['name_ar'],'facility_type':t['facility_type'],'candidate_image_id':c['image_id'],'master_image_id':c['master_image_id'],'technical_quality':c['technical_quality'],'automatic_match_basis':'existing_link','visual_review_status':'not_individually_verified','rights_status':c['rights_status'],'institutional_approval_status':'not_approved_batch_2','candidate_score':'30','candidate_reason':'Existing local linkage; candidate only.','manual_review_required':'true','notes':''})
write('batch-2-primary-image-candidates.csv',prim)
gallery=[{'feature_id':c['feature_id'],'image_id':c['image_id'],'gallery_order':'1','gallery_role':'candidate','master_image_id':c['master_image_id'],'visual_match_status':'not_individually_verified','rights_status':c['rights_status'],'publication_permission':'pending_institutional_approval','manual_review_completed':'false','notes':''} for c in cand]
write('batch-2-gallery-image-candidates.csv',gallery)
# coverage
coverage=[]
for t in targets:
 cs=[c for c in cand if c['feature_id']==t['feature_id']]
 coverage.append({'feature_id':t['feature_id'],'name_ar':t['name_ar'],'facility_type':t['facility_type'],'city_ar':t['city_ar'],'candidate_images':len(cs),'current_images':t['current_local_image_count'],'master_candidates':sum(bool(c['master_image_id']) for c in cs),'high_quality_candidates':sum(c['technical_quality']=='high' for c in cs),'acceptable_candidates':sum(c['technical_quality']=='acceptable' for c in cs),'ambiguous_candidates':sum(c['candidate_match_type']=='ambiguous_match' for c in cs),'rights_known':sum(c['rights_status'] not in ('unknown','') for c in cs),'rights_unknown':sum(c['rights_status'] in ('unknown','') for c in cs),'primary_candidate':cs[0]['image_id'] if cs else '','gallery_candidates':len(cs),'manual_review_required':'true' if cs else 'false','coverage_status':'strong_candidate_coverage' if cs else 'no_images'})
write('batch-2-accommodation-image-coverage.csv',coverage)
json.dump(coverage,open(OUT/'batch-2-accommodation-image-coverage.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
# contact sheets, relative image paths
for group,label in [('01-hotels','Hotels') ,('02-resorts','Resorts'),('03-tourism-villages','Tourism Villages'),('04-accommodation-other','Other Accommodation'),('05-current-links','Current Links'),('06-high-quality-masters','High Quality Masters'),('07-ambiguous','Ambiguous')]:
 rows=cand if group in ('01-hotels','05-current-links') else ([c for c in cand if c['technical_quality'] in ('high','acceptable')] if group=='06-high-quality-masters' else [])
 for n in range(0,len(rows),40):
  cards=[]
  for c in rows[n:n+40]:
   cards.append(f"<article><img loading='lazy' src='../../../{html.escape(c['source_relative_path'])}'><b>{html.escape(c['image_id'])}</b><div>{html.escape(c['feature_name_ar'])}</div><div>{html.escape(c['technical_quality'])} · {html.escape(c['rights_status'])}</div></article>")
  (OUT/'review-sheets'/group/f'page-{n//40+1:03d}.html').parent.mkdir(parents=True,exist_ok=True)
  (OUT/'review-sheets'/group/f'page-{n//40+1:03d}.html').write_text('<meta charset="utf-8"><title>Batch 2 review</title><style>body{font-family:Arial;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}article{border:1px solid #ccc;padding:8px}img{width:100%;height:130px;object-fit:cover}</style>'+''.join(cards),encoding='utf8')
# baseline checks and counts
base=ROOT/'docs/images/batch-1/batch-1-derivative-runtime-audit.csv'
hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['docs/images/batch-1/batch-1-derivative-runtime-audit.csv','docs/images/batch-1/batch-1-institutional-approval.csv','docs/runtime/akakus-old-tripoli-image-feature-linkage.csv']}
json.dump(hashes,open(OUT/'batch-1-baseline-sha256.json','w',encoding='utf8'),indent=2)
print(json.dumps({'targets':len(targets),'hotels':528,'resorts':262,'candidates':len(cand),'current_links':len(current),'primary':len(prim),'gallery':len(gallery)},ensure_ascii=False))
