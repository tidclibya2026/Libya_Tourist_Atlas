import csv, json, sys
from pathlib import Path
allowed={'approve_primary_candidate','approve_gallery_candidate','approve_context_only','approve_shared_same_complex','reject_wrong_facility','reject_generic','reject_duplicate','reject_quality','replace_with_master','defer','cannot_determine'}
root=Path(__file__).resolve().parents[1]
def rows(p): return list(csv.DictReader(open(root/p,encoding='utf-8-sig')))
working=rows('docs/images/batch-2a/batch-2a-review-working-set.csv'); ids={x['image_id'] for x in working}; features={x['feature_id'] for x in working}
source=Path(sys.argv[1]) if len(sys.argv)>1 else root/'docs/images/batch-2a/batch-2a-review-decisions.csv'
if not source.is_absolute(): source=root/source
if source.suffix.lower()=='.json': decisions=json.loads(source.read_text(encoding='utf-8'))
else: decisions=list(csv.DictReader(source.open(encoding='utf-8-sig')))
rejected=[]; accepted=[]; seen={}
for d in decisions:
 reason=[]
 if d.get('image_id') not in ids: reason.append('image_id_not_in_working_set')
 if d.get('feature_id') not in features: reason.append('feature_id_not_in_working_set')
 if d.get('reviewer_decision') not in allowed: reason.append('invalid_reviewer_decision')
 if d.get('reviewer_decision')=='approve_public': reason.append('approve_public_forbidden')
 if d.get('manual_review_completed','').lower()=='true' and (not d.get('reviewer_name') or not d.get('review_date')): reason.append('manual_review_requires_reviewer_and_date')
 key=(d.get('image_id'),d.get('feature_id'))
 if key in seen and seen[key].get('reviewer_decision')!=d.get('reviewer_decision'): reason.append('conflicting_decision')
 if key in seen and seen[key].get('shared_image_decision') in ('retain_shared','approve_shared_same_complex') and d.get('shared_image_decision')=='retain_for_one_feature_only': reason.append('conflicting_shared_decision')
 seen[key]=d
 if reason: rejected.append({'row':d,'reasons':reason})
 else: accepted.append(d)
print('BATCH_2A_DECISIONS_IMPORTED =',len(accepted)); print('BATCH_2A_DECISIONS_REJECTED =',len(rejected)); print('BATCH_2A_CONFLICTING_DECISIONS =',sum('conflicting_decision' in x['reasons'] for x in rejected)); print('BATCH_2A_INVALID_RIGHTS_DECISIONS =',sum('rights' in ' '.join(x['reasons']) for x in rejected))
if rejected:
 print(json.dumps(rejected,ensure_ascii=False,indent=2)); raise SystemExit(1)
