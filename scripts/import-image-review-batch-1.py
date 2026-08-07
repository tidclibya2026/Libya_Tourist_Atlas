import argparse,csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'docs/images/batch-1';P=argparse.ArgumentParser();P.add_argument('input',nargs='?',default='batch-1-review-decisions.json');a=P.parse_args();src=Path(a.input);src=src if src.is_absolute() else R/src
if not src.exists():print('BATCH_1_DECISIONS_IMPORTED = 0\nBATCH_1_DECISIONS_REJECTED = 0\nBATCH_1_CONFLICTING_DECISIONS = 0\nBATCH_1_INVALID_RIGHTS_DECISIONS = 0');raise SystemExit(0)
rows=json.loads(src.read_text(encoding='utf8')) if src.suffix.lower()=='.json' else list(csv.DictReader(src.open(encoding='utf-8-sig',newline='')));inv={x['image_id'] for x in csv.DictReader((R/'docs/images/national-image-inventory.csv').open(encoding='utf-8-sig',newline=''))};features={x['feature_id'] for x in csv.DictReader((B/'batch-1-target-feature-register.csv').open(encoding='utf-8-sig',newline=''))};allowed={'approve_public','approve_internal','approve_link_only','approve_as_context','approve_as_historical','reject_wrong_destination','reject_misleading','reject_quality','reject_rights','reject_duplicate_copy','defer','cannot_determine'};public_rights={'center_owned','ministry_owned','government_owned','official_partner_permission','photographer_permission','open_license_documented','public_domain_documented','institutional_publication_approval'};ok=[];rej=conf=badrights=0;seen={}
for x in rows:
 key=x.get('image_id');valid=key in inv and x.get('feature_id') in features and x.get('reviewer_decision') in allowed and str(x.get('manual_review_completed')).lower()=='true' and x.get('reviewer_name') and re.fullmatch(r'\d{4}-\d{2}-\d{2}',x.get('review_date',''))
 if str(x.get('manual_review_completed')).lower()=='true' and key in seen and seen[key]!=x:conf+=1;continue
 if x.get('reviewer_decision')=='approve_public' and not(x.get('publication_permission')=='public' and x.get('rights_status') in public_rights and x.get('rights_evidence')):badrights+=1;valid=False
 if valid:seen[key]=x;ok.append(x)
 else:rej+=1
if ok:
 fields=list(dict.fromkeys(k for x in ok for k in x));
 with (B/'batch-1-imported-review-decisions.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(ok)
print(f'BATCH_1_DECISIONS_IMPORTED = {len(ok)}');print(f'BATCH_1_DECISIONS_REJECTED = {rej}');print(f'BATCH_1_CONFLICTING_DECISIONS = {conf}');print(f'BATCH_1_INVALID_RIGHTS_DECISIONS = {badrights}')
