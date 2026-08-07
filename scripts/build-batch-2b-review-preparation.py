import csv,json
from pathlib import Path
ROOT=Path('.'); OUT=ROOT/'docs/images/batch-2b'; OUT.mkdir(parents=True,exist_ok=True)
def rows(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
def write(name,data,fields=None):
 if fields is None: fields=list(data[0]) if data else []
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(data)
work=rows('docs/images/batch-2a/batch-2a-review-working-set.csv'); prim=rows('docs/images/batch-2a/batch-2a-primary-recommendations.csv'); shared=rows('docs/images/batch-2a/batch-2a-shared-image-resolution.csv')
workids={x['image_id'] for x in work}; featids={x['feature_id'] for x in work}
fields=['review_id','image_id','master_image_id','feature_id','layer_id','facility_name_ar','facility_type','city_ar','automatic_match_status','visual_match_status','facility_identity_status','primary_suitability','shared_image_decision','reviewer_decision','technical_quality','rights_status','institutional_batch_approval','publication_permission','reviewer_name','review_date','manual_review_completed','decision_confidence','notes']
write('batch-2b-visual-review-decisions.csv',[],fields); (OUT/'batch-2b-review-decisions.json').write_text('[]',encoding='utf8'); write('batch-2b-review-decisions.csv',[],fields)
shared_images={x['image_id'] for x in shared}
coverage=[]
final=[]
for p in prim:
 conflict=p['current_candidate_image_id'] in shared_images
 next_action='needs_shared_conflict_resolution' if conflict else 'needs_manual_review'
 coverage.append({'feature_id':p['feature_id'],'facility_name_ar':p['facility_name_ar'],'facility_type':p['facility_type'],'primary_candidate_image_id':p['current_candidate_image_id'],'manual_review_completed':'false','visual_match_status':'cannot_determine','primary_suitability':'cannot_determine','reviewer_decision':'defer','shared_conflict_status':'unresolved' if conflict else 'none','rights_status':p['rights_status'],'institutional_approval_status':'false','next_action':next_action})
 final.append({'feature_id':p['feature_id'],'facility_name_ar':p['facility_name_ar'],'facility_type':p['facility_type'],'city_ar':'','approved_candidate_image_id':'','master_image_id':p['recommended_master_image_id'],'visual_match_status':'cannot_determine','facility_identity_status':'cannot_determine','primary_suitability':'cannot_determine','technical_quality':p['technical_quality'],'reviewer_name':'','review_date':'','rights_status':p['rights_status'],'institutional_approval_status':'false','publication_status':'pending_rights','next_action':next_action})
write('batch-2b-review-coverage.csv',coverage); write('batch-2b-primary-final-candidates.csv',final)
# shared decision tracking
sd=[]
for i,s in enumerate(shared):
 sd.append({'case_id':s.get('case_id',f'B2B-SHARED-{i+1:03d}'),'image_id':s['image_id'],'feature_ids':s['feature_ids'],'review_status':'unreviewed','shared_decision':'cannot_determine','correct_feature_id':'','manual_review_completed':'false','notes':'Awaiting human visual review.'})
write('batch-2b-shared-review-coverage.csv',sd)
json.dump({'working_set':len(work),'primary_candidates':len(prim),'shared_cases':len(shared),'manual_reviews':0},open(OUT/'batch-2b-summary.json','w',encoding='utf8'),indent=2)
print(len(work),len(prim),len(shared))
