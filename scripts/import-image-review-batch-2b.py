import csv,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(p): return list(csv.DictReader(open(root/p,encoding='utf-8-sig')))
work=read('docs/images/batch-2a/batch-2a-review-working-set.csv'); ids={x['image_id'] for x in work}; fids={x['feature_id'] for x in work}
allowed_v={'verified_correct','probably_correct','generic_context','wrong_facility','misleading','logo','map','screenshot','advertisement','personal_photo','outside_libya','ai_generated_or_uncertain','cannot_determine'}
allowed_i={'exact_facility_confirmed','facility_complex_confirmed','same_complex_uncertain_building','city_context_only','generic_accommodation','not_specific_enough','cannot_determine'}
allowed_s={'excellent_primary','acceptable_primary','gallery_only','context_only','not_suitable','cannot_determine'}
allowed_d={'approve_primary_candidate','approve_gallery_candidate','approve_context_only','reject_wrong_facility','reject_generic','reject_duplicate','reject_quality','replace_with_master','defer','cannot_determine'}
src=Path(sys.argv[1]) if len(sys.argv)>1 else root/'docs/images/batch-2b/batch-2b-review-decisions.csv'
if not src.is_absolute(): src=root/src
dec=json.loads(src.read_text(encoding='utf-8')) if src.suffix.lower()=='.json' else list(csv.DictReader(src.open(encoding='utf-8-sig')))
bad=[]; seen={}
for d in dec:
 why=[]
 if d.get('image_id') not in ids: why.append('image_id_not_in_working_set')
 if d.get('feature_id') not in fids: why.append('feature_id_not_in_working_set')
 if d.get('visual_match_status') not in allowed_v: why.append('invalid_visual_match_status')
 if d.get('facility_identity_status') not in allowed_i: why.append('invalid_facility_identity_status')
 if d.get('primary_suitability') not in allowed_s: why.append('invalid_primary_suitability')
 if d.get('reviewer_decision') not in allowed_d: why.append('invalid_reviewer_decision')
 if d.get('reviewer_decision')=='approve_public': why.append('public_approval_forbidden')
 if d.get('manual_review_completed','').lower()!='true': why.append('manual_review_completed_must_be_true')
 if not d.get('reviewer_name'): why.append('reviewer_name_required')
 if not d.get('review_date'): why.append('review_date_required')
 if d.get('visual_match_status')=='cannot_determine' and d.get('reviewer_decision') not in ('cannot_determine','defer'): why.append('cannot_determine_decision_mismatch')
 key=(d.get('image_id'),d.get('feature_id'))
 if key in seen and seen[key].get('reviewer_decision')!=d.get('reviewer_decision'): why.append('conflicting_decisions')
 seen[key]=d
 if why: bad.append({'row':d,'reasons':why})
print('BATCH_2B_DECISIONS_IMPORTED =',len(dec)-len(bad));print('BATCH_2B_DECISIONS_REJECTED =',len(bad));print('BATCH_2B_CONFLICTING_DECISIONS =',sum('conflicting_decisions' in x['reasons'] for x in bad));print('BATCH_2B_INVALID_RIGHTS_DECISIONS =',0)
if bad: print(json.dumps(bad,ensure_ascii=False,indent=2));raise SystemExit(1)
