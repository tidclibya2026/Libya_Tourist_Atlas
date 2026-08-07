import csv,json,re,hashlib,html
from pathlib import Path
from collections import defaultdict
ROOT=Path('.'); OUT=ROOT/'docs/images/batch-2a'; (OUT/'review-sheets').mkdir(parents=True,exist_ok=True)
def readcsv(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def write(name,rows,fields=None):
 if fields is None: fields=list(rows[0]) if rows else []
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
targets=readcsv('docs/images/batch-2/batch-2-target-feature-register.csv')
cands=readcsv('docs/images/batch-2/batch-2-image-candidate-register.csv')
primary=readcsv('docs/images/batch-2/batch-2-primary-image-candidates.csv')
shared=readcsv('docs/images/batch-2/batch-2-shared-image-facility-audit.csv')
# Accommodation type audit for all 790 targets; only resort layer can reveal villages.
classification=[]
for t in targets:
 text=' '.join([t.get('name_ar',''),t.get('name_en',''),t.get('facility_type',''),t.get('classification','')]).lower()
 cur=t.get('facility_type','')
 if t['layer_id']=='hotels': proposed='hotel'; basis='runtime layer hotels'; conf='high'
 elif 'tourist_village' in cur or re.search(r'قرية|village|holiday village|tourism village',text,re.I): proposed='tourism_village'; basis='facility code or explicit village term'; conf='high'
 elif cur in ('tourist_resort','family_resort','beach_resort','tourist_complex') or 'resort' in text: proposed='resort'; basis='facility code or explicit resort term'; conf='high'
 elif cur in ('review_required','accommodation_resort_other','') : proposed='unknown'; basis='insufficient internal classification evidence'; conf='low'
 else: proposed='other_accommodation'; basis='residual accommodation classification'; conf='medium'
 classification.append({'feature_id':t['feature_id'],'current_layer_id':t['layer_id'],'name_ar':t['name_ar'],'name_en':t['name_en'],'current_facility_type':cur,'proposed_facility_type':proposed,'classification_basis':basis,'confidence':conf,'manual_confirmation_required':'true' if proposed=='unknown' else 'false','notes':''})
write('batch-2a-accommodation-type-classification-audit.csv',classification)
# Working set = primary images + all shared IDs
byimg={c['image_id']:c for c in cands}
sharedids={x['image_id'] for x in shared}
workingids=set(x['candidate_image_id'] for x in primary)|sharedids
working=[byimg[i] for i in workingids if i in byimg]
for i,x in enumerate(working): x['review_item_id']=f'B2A-ITEM-{i+1:05d}'; x['review_reason']='primary_candidate' if x['image_id'] in {p['candidate_image_id'] for p in primary} else 'shared_image_case'; x['primary_candidate']='true' if x['image_id'] in {p['candidate_image_id'] for p in primary} else 'false'; x['shared_image_case']='true' if x['image_id'] in sharedids else 'false'; x['master_replacement_candidate']='true' if x.get('master_image_id') and x['master_image_id']!=x['image_id'] else 'false'; x['automatic_match_basis']='existing_link'; x['manual_review_required']='true'; x.setdefault('city_ar','')
fields=['review_item_id','image_id','source_relative_path','master_image_id','feature_id','layer_id','feature_name_ar','facility_type','city_ar','review_reason','primary_candidate','shared_image_case','master_replacement_candidate','technical_quality','automatic_match_basis','rights_status','manual_review_required','notes']
write('batch-2a-review-working-set.csv',working,fields)
# Shared resolution rows
res=[]
for i,s in enumerate(shared):
 ids=s.get('feature_ids','').split('|'); names=s.get('facility_names',''); cities=s.get('cities','')
 res.append({'case_id':f'B2A-SHARED-{i+1:03d}','image_id':s.get('image_id',''),'feature_ids':s.get('feature_ids',''),'facility_names':names,'cities':cities,'relationship_status':'cannot_determine','shared_use_allowed':'false','primary_use_allowed':'false','recommended_owner_feature_id':'','recommended_action':'requires_manual_review','manual_visual_review_required':'true','decision_source':'automatic_shared-image detection only','confidence':'low','notes':'No automatic cross-facility approval; identity must be visually reviewed.'})
write('batch-2a-shared-image-resolution.csv',res)
# decisions blank
decf=['review_id','image_id','master_image_id','feature_id','layer_id','facility_name_ar','facility_type','city_ar','automatic_match_status','visual_match_status','facility_identity_status','primary_suitability','shared_image_decision','reviewer_decision','technical_quality','rights_status','institutional_batch_approval','publication_permission','reviewer_name','review_date','manual_review_completed','decision_confidence','notes']
write('batch-2a-visual-review-decisions.csv',[],decf)
# primary recommendations
pr=[]
for p in primary:
 pr.append({'feature_id':p['feature_id'],'facility_name_ar':p['feature_name_ar'],'facility_type':p['facility_type'],'city_ar':'','current_candidate_image_id':p['candidate_image_id'],'recommended_image_id':p['candidate_image_id'],'recommended_master_image_id':p['master_image_id'],'automatic_match_basis':p['automatic_match_basis'],'technical_quality':p['technical_quality'],'shared_image_status':'shared_case_requires_review' if p['candidate_image_id'] in sharedids else 'not_shared_detected','manual_visual_review_status':'not_individually_verified','primary_suitability':'cannot_determine','rights_status':p['rights_status'],'institutional_approval_status':'not_approved_batch_2a','recommendation_status':'shared_image_conflict' if p['candidate_image_id'] in sharedids else 'ready_for_manual_review','notes':''})
write('batch-2a-primary-recommendations.csv',pr)
# technical score
tech=[]
for p in primary:
 c=byimg.get(p['candidate_image_id'],{})
 tech.append({'feature_id':p['feature_id'],'image_id':p['candidate_image_id'],'technical_quality':p['technical_quality'],'resolution':'recorded_in_phase_1_inventory','aspect_ratio':'recorded_in_phase_1_inventory','sharpness_available':'not_recomputed','brightness_available':'not_recomputed','file_health':'valid_linkage_record','master_status':'master_candidate' if p['master_image_id'] else 'distinct_candidate','watermark_detectable_if_metadata_or_visual_review':'requires_manual_review','duplicate_status':'candidate_only','notes':''})
write('batch-2a-primary-technical-score.csv',tech)
# no-image facilities
without=[t for t in targets if t['feature_id'] not in {p['feature_id'] for p in primary}]
noimg=[{'feature_id':t['feature_id'],'name_ar':t['name_ar'],'facility_type':t['facility_type'],'city_ar':t['city_ar'],'municipality_ar':t.get('municipality_ar',''),'classification':t.get('classification',''),'stars':t.get('stars',''),'candidate_count':'0','possible_remote_reference':'false','priority_for_future_collection':'A' if t['facility_type'] in ('tourist_resort','tourist_village') else 'B','recommended_collection_method':'institutional or facility-provided image request','notes':''} for t in without]
write('batch-2a-facilities-without-images.csv',noimg)
# rights plan one row per primary feature
rights=[{'feature_id':p['feature_id'],'facility_name_ar':p['feature_name_ar'],'image_id':p['candidate_image_id'],'current_rights_status':p['rights_status'],'likely_rights_holder':'unknown','evidence_available':'none in local rights register','required_confirmation':'documented permission or institutional source record','recommended_contact':'facility_management','publication_blocker':'true','priority':'A','notes':'Likely holder is not ownership evidence.'} for p in primary]
write('batch-2a-rights-clearance-plan.csv',rights)
# contact sheets <=30
groups=[('01-primary-hotels',[x for x in working if x['layer_id']=='hotels']),('02-primary-resorts',[x for x in working if x['layer_id']=='resorts']),('03-tourism-villages-if-found',[x for x in working if any(y['feature_id']==x['feature_id'] and y['proposed_facility_type']=='tourism_village' for y in classification)]),('04-shared-image-cases',[x for x in working if x['image_id'] in sharedids]),('05-high-quality-primary',[x for x in working if x.get('technical_quality')=='high']),('06-acceptable-primary',[x for x in working if x.get('technical_quality')=='acceptable']),('07-master-replacements',[x for x in working if x.get('master_replacement_candidate')=='true'])]
for dirname,rows in groups:
 for n in range(0,len(rows),30):
  cards=[]
  for x in rows[n:n+30]:
   src='../../../../'+x['source_relative_path']
   cards.append(f"<article><img loading='lazy' src='{html.escape(src)}'><b>{html.escape(x['image_id'])}</b><div>{html.escape(x['feature_name_ar'])}</div><div>{html.escape(x.get('facility_type',''))} · {html.escape(x.get('technical_quality',''))}</div><div>Feature: {html.escape(x['feature_id'])}</div><div>Rights: {html.escape(x.get('rights_status','unknown'))}</div></article>")
  p=OUT/'review-sheets'/dirname/f'page-{n//30+1:03d}.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('<meta charset="utf-8"><title>Batch 2A review</title><style>body{font-family:Arial;display:grid;grid-template-columns:repeat(3,1fr);gap:10px}article{border:1px solid #bbb;padding:8px}img{width:100%;height:130px;object-fit:cover}</style>'+''.join(cards),encoding='utf8')
# summary
summary={'working_images':len(working),'primary_images':len({x['candidate_image_id'] for x in primary}),'shared_images':len(sharedids),'master_replacements':sum(x['master_replacement_candidate']=='true' for x in working),'high':sum(x['technical_quality']=='high' for x in primary),'acceptable':sum(x['technical_quality']=='acceptable' for x in primary),'low':sum(x['technical_quality'] not in ('high','acceptable') for x in primary),'without_images':len(noimg),'contact_sheets':len(list((OUT/'review-sheets').rglob('*.html')))}
json.dump(summary,open(OUT/'batch-2a-summary.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
print(json.dumps(summary,ensure_ascii=False))
