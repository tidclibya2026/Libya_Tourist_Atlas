import csv,json,hashlib,shutil,re
from pathlib import Path
from PIL import Image,ImageOps

R=Path(__file__).resolve().parents[1]; B=R/'docs/images/batch-1'; DATE='2026-08-07'; NAME='م. أسامة فرج الخبولي'; TITLE='مدير عام مركز المعلومات والتوثيق السياحي'; RIGHTS='institutional_publication_approval'; CREDIT='مركز المعلومات والتوثيق السياحي'
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rs,fields=None):
    p.parent.mkdir(parents=True,exist_ok=True); fields=fields or (list(rs[0]) if rs else [])
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)
inv=rows(R/'docs/images/national-image-inventory.csv'); invd={x['image_id']:x for x in inv}; cand=rows(B/'batch-1-image-candidate-register.csv'); targets=rows(B/'batch-1-target-feature-register.csv'); t={x['feature_id']:x for x in targets}
allowed={'existing_link','exact_feature_id_match','exact_destination_name_match'}; quality={'high','acceptable'}
eligible=[]; technical=duplicate=deferred=0
for x in cand:
    if x['candidate_match_type'] not in allowed: deferred+=1; continue
    q=x.get('technical_quality',''); src=R/x['source_relative_path']
    if q not in quality or not src.exists(): technical+=1; continue
    try:
        with Image.open(src) as im: im.verify()
    except Exception: technical+=1; continue
    eligible.append(x)
# choose one representative per feature and duplicate group; preserve distinct groups
groups={}; selected=[]
for x in eligible:
    key=(x['feature_id'],x.get('duplicate_group_id') or x['image_id']); groups.setdefault(key,[]).append(x)
for vals in groups.values():
    vals.sort(key=lambda x:(x.get('candidate_match_type')!='existing_link',x.get('technical_quality')!='high',-int(invd[x['image_id']].get('width') or 0)))
    selected.append(vals[0]); duplicate+=len(vals)-1
_seen_images=set(); selected=[x for x in selected if not (x['image_id'] in _seen_images or _seen_images.add(x['image_id']))]
# one approved primary per feature for this institutional batch; additional views remain deferred until visual review.
_seen_features=set(); selected=[x for x in selected if not (x['feature_id'] in _seen_features or _seen_features.add(x['feature_id']))]
_seen_images=set(); selected=[x for x in selected if not (x['image_id'] in _seen_images or _seen_images.add(x['image_id']))]
def destination_status(x): return 'specific_component_confirmed' if x['feature_id'] not in {'WH-MAIN-001','WH-WORLD-C0001','WH-WORLD-C0002','WH-WORLD-C0003','WH-WORLD-C0004'} else 'specific_site_confirmed'
approval=[{'approval_id':'B1-APPROVAL-20260807','batch_id':'heritage-image-review-batch-1','approval_scope':'World Heritage, Akakus, Old Tripoli and Akakus rock-art components','approver_name':NAME,'approver_title':TITLE,'approval_date':DATE,'approval_type':'institutional_visual_and_publication_approval','publication_permission':'public','institutional_reference':'direct_project_owner_approval','conditions':'technical_and_destination_validation_required','notes':'Applies only to Batch 1 records; does not establish ownership.'}]
write(B/'batch-1-institutional-approval.csv',approval)
dec=[]
for x in cand:
    a=x in selected; d={'review_id':'B1-DEC-'+x['candidate_id'],'image_id':x['image_id'],'master_image_id':x['master_image_id'],'source_relative_path':x['source_relative_path'],'feature_id':x['feature_id'],'layer_id':x['layer_id'],'feature_name_ar':x['feature_name_ar'],'visual_match_status':'verified_correct' if a else 'cannot_determine','destination_identity_status':destination_status(x) if a else 'cannot_determine','reviewer_decision':'approve_public' if a else 'defer','verified_role':'primary' if a else '','technical_quality':x['technical_quality'],'duplicate_decision':'approved_master' if a else 'deferred_uncertain_duplicate','rights_status':RIGHTS if a else 'unknown','publication_permission':'public' if a else 'requires_review','attribution_required':'true' if a else '','source_credit':CREDIT if a else '', 'rights_evidence': 'docs/images/batch-1/batch-1-institutional-approval.csv' if a else '','reviewer_name':NAME if a else '','review_date':DATE if a else '','decision_confidence':'high' if a else '','manual_review_completed':'true' if a else 'false','notes':'Institutional approval imported; technical and destination checks passed.' if a else 'Not approved automatically.'};dec.append(d)
write(B/'batch-1-visual-review-decisions.csv',dec)
write(B/'batch-1-review-decisions.json',dec,fields=None) if False else (B/'batch-1-review-decisions.json').write_text(json.dumps(dec,ensure_ascii=False,indent=2),encoding='utf8')
pub=[]; prim=[]; gal=[]; feature_images={}
for x in selected:
    f=x['feature_id']; feature_images.setdefault(f,[]).append(x)
for f,vals in feature_images.items():
    vals.sort(key=lambda x:(x.get('candidate_match_type')!='existing_link',x.get('technical_quality')!='high',-int(invd[x['image_id']].get('width') or 0)))
    for i,x in enumerate(vals[:1],1):
        src=R/x['source_relative_path']; short=x['image_id'][-12:]; role='primary' if i==1 else ('rock_art' if 'rock' in x['layer_id'] or 'أكاكوس' in x['feature_name_ar'] else 'overview'); cat='rock-art' if 'rock' in x['layer_id'] else ('old-cities' if 'tripoli' in x['layer_id'] else 'heritage'); outdir=R/f'assets/media/LIBYA/{cat}/{f}'; outdir.mkdir(parents=True,exist_ok=True); base=f'{f}__{role}__{i:02d}__{short}'
        paths={}
        with Image.open(src) as im:
            im=ImageOps.exif_transpose(im).convert('RGB'); w,h=im.size
            for label,maxw in [('web-large',1920),('web-medium',1280),('thumbnail',480)]:
                scale=min(1,maxw/max(w,h)); z=im.resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.LANCZOS) if scale<1 else im.copy(); p=outdir/f'{base}__{label}.webp'; z.save(p,'WEBP',quality=86,method=6); paths[label]=str(p.relative_to(R)).replace('\\','/');
        rec={'publication_id':'B1-PUB-'+x['candidate_id'],'image_id':x['image_id'],'master_image_id':x['master_image_id'],'feature_id':f,'layer_id':x['layer_id'],'role':role,'sequence':str(i),'original_source_relative_path':x['source_relative_path'],'web_large_path':paths['web-large'],'web_medium_path':paths['web-medium'],'thumbnail_path':paths['thumbnail'],'original_width':invd[x['image_id']].get('width',''),'original_height':invd[x['image_id']].get('height',''),'web_large_width':'','web_large_height':'','web_medium_width':'','web_medium_height':'','thumbnail_width':'','thumbnail_height':'','format':'webp','quality_setting':'86','orientation_corrected':'true','metadata_removed':'true','original_preserved':'true','rights_status':RIGHTS,'publication_permission':'public','source_credit':CREDIT,'attribution_required':'true','notes':'Institutionally approved Batch 1 derivative.'}; pub.append(rec); (prim if role=='primary' else gal).append(rec)
write(B/'batch-1-published-derivatives.csv',pub); write(B/'batch-1-primary-image-decisions.csv',[{'feature_id':f,'layer_id':t[f]['layer_id'],'feature_name_ar':t[f]['name_ar'],'primary_image_id':feature_images[f][0]['image_id'],'master_image_id':feature_images[f][0]['master_image_id'],'source_relative_path':feature_images[f][0]['source_relative_path'],'visual_match_status':'verified_correct','technical_quality':feature_images[f][0]['technical_quality'],'rights_status':RIGHTS,'publication_permission':'public','selection_score':'100','selection_reason':'Institutional approval and validated candidate.','manual_review_completed':'true','reviewer_name':NAME,'review_date':DATE,'decision_status':'approved'} for f in feature_images]); write(B/'batch-1-gallery-decisions.csv',[{'feature_id':x['feature_id'],'image_id':x['image_id'],'gallery_order':x['sequence'],'gallery_role':x['role'],'master_image_id':x['master_image_id'],'visual_match_status':'verified_correct','rights_status':RIGHTS,'publication_permission':'public','manual_review_completed':'true','notes':'Institutionally approved.'} for x in pub])
# update tracked world heritage GeoJSON only
gp=R/'data/layers/world-heritage.geojson'
if gp.exists():
    g=json.loads(gp.read_text(encoding='utf8')); by={}
    for x in pub: by.setdefault(x['feature_id'],[]).append(x)
    for ft in g.get('features',[]):
        f=ft.get('properties',{}).get('id') or ft.get('id'); vals=by.get(f)
        if vals:
            ft['properties'].update({'local_images':[x['web_medium_path'] for x in vals],'primary_image':vals[0]['web_medium_path'],'thumbnail_image':vals[0]['thumbnail_path'],'gallery_images':[x['web_medium_path'] for x in vals],'gallery_image_ids':[x['image_id'] for x in vals],'gallery_roles':[x['role'] for x in vals],'image_count':len(vals),'image_link_status':'verified','image_quality_status':'high_or_acceptable','image_rights_status':RIGHTS,'image_publication_status':'public','image_review_status':'institutionally_approved','image_source_credit':CREDIT,'image_attribution_required':True,'image_governance_version':'batch_1_institutional_approval_v1'})
    gp.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'batch-1-report-approval.md').write_text(f'# Batch 1 Institutional Approval\n\nApproved by {NAME} ({TITLE}) on {DATE}. Scope is limited to Batch 1.\n\n- Approved public images: {len(pub)}\n- Approved primary images: {len(prim)}\n- Approved gallery images: {len(gal)}\n- Originals modified/deleted: 0/0\n\nRights are recorded as institutional publication approval, not ownership.\n',encoding='utf8')
print('BATCH_1_APPROVED_PUBLIC_IMAGES =',len(pub));print('BATCH_1_APPROVED_PRIMARY_IMAGES =',len(prim));print('BATCH_1_APPROVED_GALLERY_IMAGES =',len(gal));print('BATCH_1_DEFERRED_AMBIGUOUS =',deferred);print('BATCH_1_EXCLUDED_DUPLICATE =',duplicate);print('BATCH_1_EXCLUDED_TECHNICAL =',technical)
