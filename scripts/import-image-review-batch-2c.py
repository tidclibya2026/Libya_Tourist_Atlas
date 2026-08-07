#!/usr/bin/env python3
"""Validate imported human decisions for Batch 2C; never changes images or GeoJSON."""
import csv, datetime, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'docs/images/batch-2c/batch-2c-first-25-register.csv'
ALLOWED_DECISIONS = {'approve_primary_candidate','approve_gallery_candidate','approve_context_only','reject_wrong_facility','reject_generic','reject_quality','replace_with_master','defer','cannot_determine'}
ALLOWED_VISUAL = {'verified_correct','probably_correct','generic_context','wrong_facility','misleading','cannot_determine'}
ALLOWED_IDENTITY = {'exact_facility_confirmed','facility_complex_confirmed','same_complex_uncertain_building','city_context_only','generic_accommodation','not_specific_enough','cannot_determine'}
ALLOWED_PRIMARY = {'excellent_primary','acceptable_primary','gallery_only','context_only','not_suitable','cannot_determine'}

def main(path):
    rows = list(csv.DictReader(REGISTER.open(encoding='utf-8-sig', newline='')))
    allowed = {(r['image_id'], r['feature_id']) for r in rows}
    decisions = json.loads(Path(path).read_text(encoding='utf-8')) if str(path).endswith('.json') else list(csv.DictReader(Path(path).open(encoding='utf-8-sig', newline='')))
    errors=[]; seen=set()
    for i,d in enumerate(decisions,1):
        key=(d.get('image_id',''),d.get('feature_id',''))
        if key not in allowed: errors.append(f'row {i}: image/feature outside first 25')
        if key in seen: errors.append(f'row {i}: duplicate review')
        seen.add(key)
        if d.get('reviewer_decision') not in ALLOWED_DECISIONS: errors.append(f'row {i}: invalid reviewer_decision')
        if d.get('visual_match_status') not in ALLOWED_VISUAL: errors.append(f'row {i}: invalid visual_match_status')
        if d.get('facility_identity_status') not in ALLOWED_IDENTITY: errors.append(f'row {i}: invalid facility_identity_status')
        if d.get('primary_suitability') not in ALLOWED_PRIMARY: errors.append(f'row {i}: invalid primary_suitability')
        if d.get('reviewer_decision') == 'approve_public' or d.get('publication_permission') == 'public': errors.append(f'row {i}: public approval forbidden')
        if str(d.get('institutional_batch_approval','')).lower() == 'true': errors.append(f'row {i}: institutional approval forbidden')
        if str(d.get('manual_review_completed','')).lower() != 'true': errors.append(f'row {i}: manual_review_completed must be true')
        if not d.get('reviewer_name') or not d.get('review_date'): errors.append(f'row {i}: reviewer and date required')
        try: datetime.date.fromisoformat(d.get('review_date',''))
        except ValueError: errors.append(f'row {i}: invalid review date')
        if d.get('rights_status') not in ('unknown','pending','requires_review',''): errors.append(f'row {i}: rights status changed or invented')
    print(f'BATCH_2C_DECISIONS_IMPORTED = {len(decisions)-len(errors)}')
    print(f'BATCH_2C_DECISIONS_REJECTED = {len(errors)}')
    for e in errors: print('ERROR = '+e)
    return 1 if errors else 0

if __name__ == '__main__':
    if len(sys.argv)!=2: print('usage: import-image-review-batch-2c.py DECISIONS.json|csv'); raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
