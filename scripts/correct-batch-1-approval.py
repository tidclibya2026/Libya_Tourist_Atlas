import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; B=R/'docs/images/batch-1'; APPROVER='م. أسامة فرج الخبولي'; DATE='2026-08-07'; RIGHTS='institutional_publication_approval'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 fields=list(rows[0]) if rows else []
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
dec=read(B/'batch-1-visual-review-decisions.csv'); approved={x['image_id'] for x in read(B/'batch-1-imported-review-decisions.csv')}
for x in dec:
 x['institutional_batch_approval']='true' if x['image_id'] in approved else 'false'; x['institutional_approver_name']=APPROVER if x['image_id'] in approved else ''; x['institutional_approval_date']=DATE if x['image_id'] in approved else ''; x['institutional_publication_scope']='batch_1_candidate_images' if x['image_id'] in approved else ''
 if x['image_id'] in approved:
  x.update(manual_review_completed='false',visual_match_status='cannot_determine',destination_identity_status='cannot_determine',reviewer_decision='defer',reviewer_name='',review_date='',decision_confidence='',rights_status=RIGHTS,publication_permission='public')
write(B/'batch-1-visual-review-decisions.csv',dec)
pub=read(B/'batch-1-published-derivatives.csv'); targets={x['feature_id']:x for x in read(B/'batch-1-target-feature-register.csv')}; world=set()
g=json.loads((R/'data/layers/world-heritage.geojson').read_text(encoding='utf8'))
for x in g.get('features',[]): world.add(x.get('properties',{}).get('id') or x.get('id'))
link=[]
for x in pub:
 fid=x['feature_id']; layer=x['layer_id']; actual={'world-heritage':'data/layers/world-heritage.geojson','akakus':'data/kml/final/akakus.kml','old-tripoli':'data/kml/final/old-tripoli.kml'}.get(layer,''); exists=(fid in world) if layer=='world-heritage' else (fid in targets)
 x['corrected_publication_status']='provisional_publication_candidate' if exists else 'withheld_pending_linkage'; x['image_review_status']='institutionally_approved_pending_visual_verification'; x['image_link_status']='technically_valid_pending_visual_verification'; x['image_publication_status']='provisional_publication_candidate';
 link.append({'image_id':x['image_id'],'feature_id':fid,'declared_layer_id':layer,'actual_layer_file':actual,'feature_exists':str(exists).lower(),'old_linkage_status':'published','new_linkage_status':'linked_provisional' if exists else 'withheld_pending_linkage','geojson_updated':'true' if exists else 'false','notes':'Institutional approval is separate from individual visual verification.'})
write(B/'batch-1-layer-linkage-correction.csv',link)
audit=[]
for x in pub:
 l=next(y for y in link if y['image_id']==x['image_id']); audit.append({'image_id':x['image_id'],'feature_id':x['feature_id'],'layer_id':x['layer_id'],'source_relative_path':x['original_source_relative_path'],'derivative_paths':x['web_large_path']+'|'+x['web_medium_path']+'|'+x['thumbnail_path'],'institutional_batch_approval':'true','manual_review_completed':'false','visual_match_status':'cannot_determine','technical_status':'valid','rights_status':RIGHTS,'current_publication_status':'public','corrected_publication_status':l['new_linkage_status'],'recommended_action':'withhold_until_linkage_corrected' if l['feature_exists']!='true' else 'retain_as_provisional_candidate','notes':'No individual visual review imported.'})
write(B/'batch-1-provisional-publication-audit.csv',audit)
for p in [R/'data/layers/world-heritage.geojson']:
 if p.exists():
  g=json.loads(p.read_text(encoding='utf8'))
  for f in g.get('features',[]):
   pr=f.get('properties',{}); fid=pr.get('id') or f.get('id'); vals=[x for x in pub if x['feature_id']==fid]
   if vals: pr.update(image_review_status='institutionally_approved_pending_visual_verification',image_publication_status='provisional_publication_candidate',image_link_status='technically_valid_pending_visual_verification',image_rights_status=RIGHTS,image_governance_version='batch_1_institutional_approval_correction_v1');
  p.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'batch-1-approval-correction-report.md').write_text('# Batch 1 approval correction\n\nInstitutional approval is recorded separately from individual visual verification. All 74 previously published candidates are now provisional; individual review fields are reset to defer/not individually verified. World Heritage links are retained provisionally where IDs exist. Akakus and Old Tripoli candidates are withheld pending actual layer linkage.\n\nStatus: BATCH_1_INSTITUTIONAL_APPROVAL_RECORDED\nStatus: BATCH_1_PENDING_INDIVIDUAL_VISUAL_VERIFICATION\n',encoding='utf8')
print('INSTITUTIONALLY_APPROVED_IMAGES',len(approved));print('WORLD_HERITAGE_APPROVED_IMAGES',sum(x['layer_id']=='world-heritage' for x in pub));print('AKAKUS_APPROVED_IMAGES',sum(x['layer_id']=='akakus' for x in pub));print('OLD_TRIPOLI_APPROVED_IMAGES',sum(x['layer_id']=='old-tripoli' for x in pub));print('ROCK_ART_APPROVED_IMAGES',sum(x['layer_id']=='rock-art' for x in pub))
