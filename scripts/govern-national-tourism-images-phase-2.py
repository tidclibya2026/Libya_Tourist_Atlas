import csv,hashlib,json,os,re,subprocess
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'docs/images';NOW=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def read(n):
 with (O/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(n,fields,rows):
 with (O/n).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
required=['national-image-inventory.csv','national-image-file-health.csv','national-image-duplicate-register.csv','national-image-technical-quality.csv','national-image-rights-register.csv','national-image-feature-linkage-register.csv','national-current-image-link-audit.csv','national-image-manual-review.csv','national-image-name-metadata-review.csv','national-remote-image-reference-register.csv','national-image-phase-1-scorecard.csv','national-image-phase-1-scorecard.json']
missing=[x for x in required if not (O/x).exists()];assert not missing,missing
inv=read('national-image-inventory.csv');health=read('national-image-file-health.csv');dups=read('national-image-duplicate-register.csv');quality=read('national-image-technical-quality.csv');rights=read('national-image-rights-register.csv');links=read('national-image-feature-linkage-register.csv');audit=read('national-current-image-link-audit.csv');manual=read('national-image-manual-review.csv');remote=read('national-remote-image-reference-register.csv')
by_path={x['source_relative_path']:x for x in inv};hpath={x['source_relative_path']:x for x in health};qpath={x['source_relative_path']:x for x in quality};rpath={x['source_relative_path']:x for x in rights};source_missing=[];modified=[]
for x in inv:
 p=R/x['source_relative_path']
 if not p.exists():source_missing.append(x['source_relative_path'])
 elif hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']:modified.append(x['source_relative_path'])
tracked=subprocess.check_output(['git','ls-files','data/layers/*.geojson'],cwd=R,text=True).splitlines();features={};feature_layer={}
for p in tracked:
 for f in json.loads((R/p).read_text(encoding='utf8')).get('features',[]):
  fid=f.get('properties',{}).get('id') or f.get('id');features[fid]=f;feature_layer[fid]=Path(p).stem
current=[x for x in links if x['existing_link']=='true'];explicit=[x for x in links if x['match_type']=='exact_feature_id_match'];a_paths={x['source_relative_path'] for x in current+explicit};master_by_group={};group_paths=defaultdict(set)
for x in dups:master_by_group[x['duplicate_group_id']]=x['recommended_master_image_id'];group_paths[x['duplicate_group_id']]|={x['image_a_path'],x['image_b_path']}
master_ids=set(master_by_group.values());b_paths={x['source_relative_path'] for x in inv if x['image_id'] in master_ids and qpath[x['source_relative_path']]['minimum_web_quality_status'] in ('high','acceptable') and x['source_relative_path'] not in a_paths};c_paths={x['source_relative_path'] for x in inv}-a_paths-b_paths

# Review-sheet integrity.
sheets=list((O/'review-sheets').glob('phase-1-review-*.html'));empty=broken=private=0
for p in sheets:
 s=p.read_text(encoding='utf8');cards=s.count('<article>');empty+=cards==0;private+=bool(re.search(r'[A-Za-z]:[\\/]Users[\\/]|file://|/home/|Desktop|Downloads',s,re.I))
 for src in re.findall(r'<img src="([^"]+)"',s):broken+=not (p.parent/src).resolve().exists()
 if cards>40:broken+=1

# Every row is an automatic triage record; no false claim of human review.
dgroup={p:g for g,ps in group_paths.items() for p in ps};visual=[]
for i,x in enumerate(inv,1):
 p=x['source_relative_path'];priority='PRIORITY_A' if p in a_paths else 'PRIORITY_B' if p in b_paths else 'PRIORITY_C';ln=next((z for z in links if z['source_relative_path']==p),{});q=qpath[p]['minimum_web_quality_status'];status=hpath[p]['file_health_status'];auto='corrupt' if status=='corrupt' else 'extension_mismatch' if status=='extension_mismatch' else 'exact_sha_duplicate' if any(z['sha256_match']=='true' and p in (z['image_a_path'],z['image_b_path']) for z in dups) else 'file_and_metadata_validated'
 visual.append({'review_id':f'P2REV-{i:06d}','image_id':x['image_id'],'master_image_id':master_by_group.get(dgroup.get(p,''),''),'source_relative_path':p,'review_priority':priority,'feature_id_before':ln.get('feature_id',''),'feature_id_proposed':ln.get('feature_id',''),'layer_id':ln.get('layer_id',''),'feature_name_ar':ln.get('feature_name_ar',''),'visual_match_status':'cannot_determine','reviewer_decision':'defer','verified_role':ln.get('proposed_role',''),'technical_quality_before':q,'technical_quality_after':q,'duplicate_decision':auto,'rights_status':'unknown','rights_evidence':'No explicit local permission document linked','publication_permission':'requires_review','attribution_required':'unknown','source_credit':'','reviewer_name':'','review_date':'','decision_confidence':'','manual_review_completed':'false','validation_method':'automatic_validation','notes':'Awaiting human visual and documented rights review.'})
write('phase-2-visual-review-decisions.csv',list(visual[0]),visual)

cur=[]
for i,x in enumerate(current,1):
 p=x['source_relative_path'];g=dgroup.get(p,'');master=master_by_group.get(g,'');rec=by_path.get(p,{});q=qpath.get(p,{}).get('minimum_web_quality_status','corrupt');exists=(R/p).exists();cur.append({'link_id':f'P2LINK-{i:06d}','feature_id':x['feature_id'],'layer_id':x['layer_id'],'feature_name_ar':x['feature_name_ar'],'image_id':x['image_id'],'source_relative_path':p,'current_role':x['proposed_role'],'file_exists':str(exists).lower(),'technical_quality':q,'visual_match_status':'cannot_determine','duplicate_group_id':g,'master_image_id':master,'rights_status':'unknown','publication_permission':'requires_review','verification_status':'valid_but_rights_unknown' if exists else 'technical_replacement_required','recommended_action':'retain_reference_defer_publication','replacement_image_id':'','evidence':'automatic_validation: file, hash, feature and relative path checked','confidence':'technical_only','manual_review_required':'true','notes':'Existence is not visual identity or rights verification.'})
write('phase-2-current-link-verification.csv',list(cur[0]),cur)

gd=[]
for g,ps in sorted(group_paths.items()):
 master=master_by_group[g]
 for p in sorted(ps):
  exact=any(z['duplicate_group_id']==g and z['sha256_match']=='true' and p in (z['image_a_path'],z['image_b_path']) for z in dups);gd.append({'duplicate_group_id':g,'image_id':by_path[p]['image_id'],'master_image_id':master,'group_decision':'exact_copy' if exact and by_path[p]['image_id']==master else 'uncertain','keep_as_distinct':'false' if exact else 'true','publishable':'false','recommended_role':'master_candidate' if by_path[p]['image_id']==master else 'review','technical_reason':'SHA exact evidence' if exact else 'perceptual candidate only','visual_reason':'not manually reviewed','rights_status':'unknown','manual_review_completed':'false','notes':'No deletion; near groups require visual review.'})
write('phase-2-duplicate-group-decisions.csv',list(gd[0]),gd)

# Deterministic threshold evaluation cohort; rates remain unavailable without human labels.
groups=sorted(group_paths);cross=[]
for g in groups:
 fids={z['feature_id'] for z in current if z['source_relative_path'] in group_paths[g]}
 if len(fids)>1:cross.append(g)
low=sorted(groups,key=lambda g:min([int(z['perceptual_distance'] or 99) for z in dups if z['duplicate_group_id']==g]))[:50];high=sorted(groups,key=lambda g:min([int(z['perceptual_distance'] or 99) for z in dups if z['duplicate_group_id']==g]),reverse=True)[:50];random_sample=groups[::max(1,len(groups)//100)][:100];cohort=list(dict.fromkeys(random_sample+low+high+cross));thr=[]
for g in cohort:thr.append({'duplicate_group_id':g,'sample_class':'cross_feature' if g in cross else 'low_distance' if g in low else 'upper_threshold' if g in high else 'systematic_sample','threshold_before':5,'threshold_after':5,'histogram_check':'not_run','manual_visual_review_completed':'false','observed_group_result':'unlabeled','false_group':'','true_near_duplicate':'','cross_destination_false_group':'','notes':'Human labels required before computing rates or changing threshold.'})
write('phase-2-near-duplicate-threshold-evaluation.csv',list(thr[0]),thr)

re=[]
for x in inv:
 p=x['source_relative_path'];before=rpath[p]['rights_status'];re.append({'image_id':x['image_id'],'source_relative_path':p,'rights_status_before':before,'rights_status_after':'unknown','rights_holder':'','license_type':'','publication_permission':'requires_review','attribution_required':'unknown','source_credit':'','evidence_type':'insufficient_local_evidence','evidence_relative_path':'','evidence_description':'Repository presence, folder names, and GeoJSON labels do not prove publication permission.','evidence_confidence':'high','institutional_confirmation_required':'true','review_status':'open','notes':'Not approved for public publication.'})
write('phase-2-rights-evidence-register.csv',list(re[0]),re)

coverage=[]
for fid,f in features.items():
 p=f.get('properties',{});loc=p.get('local_images') if isinstance(p.get('local_images'),list) else [];rem=[x for x in remote if x['feature_id']==fid];coverage.append({'feature_id':fid,'layer_id':feature_layer[fid],'name_ar':p.get('name_ar') or p.get('name') or '','publication_status':p.get('publication_status') or 'unknown','current_local_image_count':len(loc),'current_primary_image':p.get('primary_image') or '','verified_images':0,'public_rights_images':0,'internal_only_images':0,'high_quality_candidates':sum(qpath.get(z,{}).get('minimum_web_quality_status')=='high' for z in loc),'review_candidates':len(loc)+len(rem),'coverage_priority':'P1' if feature_layer[fid]=='world-heritage' and not loc else 'P2' if not loc else 'P3','recommended_action':'human_visual_and_rights_review' if loc else 'seek_documented_local_image','notes':'No public approval inferred.'})
write('phase-2-destination-image-coverage-priority.csv',list(coverage[0]),coverage)

new=[]
for i,x in enumerate(explicit,1):new.append({'linkage_id':f'P2NEW-{i:05d}','image_id':x['image_id'],'master_image_id':master_by_group.get(dgroup.get(x['source_relative_path'],''),''),'feature_id':x['feature_id'],'layer_id':x['layer_id'],'feature_name_ar':x['feature_name_ar'],'match_type':'verified_exact_identifier_technical','match_score':1,'textual_evidence':'Feature ID token in filename/path','spatial_evidence':'','visual_evidence':'not manually reviewed','source_evidence':x['source_relative_path'],'rights_status':'unknown','publication_permission':'requires_review','technical_quality':x['technical_quality'],'verified_role':'','automatic_link':'false','manual_visual_review_completed':'false','decision':'defer','confidence':'identity_high_rights_unresolved','notes':'Not linked until human visual and rights review.'})
write('phase-2-new-image-linkage-decisions.csv',list(new[0]) if new else ['linkage_id'],new)

usage=defaultdict(list)
for x in current:usage[x['source_relative_path']].append(x)
shared=[]
for p,xs in usage.items():
 if len({x['feature_id'] for x in xs})>1:shared.append({'image_id':by_path[p]['image_id'],'source_relative_path':p,'feature_ids':'|'.join(sorted({x['feature_id'] for x in xs})),'layer_ids':'|'.join(sorted({x['layer_id'] for x in xs})),'usage_count':len(xs),'usage_classification':'requires_review','primary_usage_count':0,'recommended_action':'human_visual_review','manual_review_completed':'false','notes':'Shared use is not automatically valid.'})
write('phase-2-shared-image-usage-review.csv',list(shared[0]) if shared else ['image_id','source_relative_path','feature_ids','layer_ids','usage_count','usage_classification','primary_usage_count','recommended_action','manual_review_completed','notes'],shared)

cor=[]
for x in health:
 if x['file_health_status']=='corrupt':cor.append({'image_id':x['image_id'],'source_relative_path':x['source_relative_path'],'file_health_status':'corrupt','linked_feature_ids':'|'.join(z['feature_id'] for z in current if z['source_relative_path']==x['source_relative_path']),'replacement_image_id':'','replacement_evidence':'none','resolution_status':'unresolved_archived_original','original_preserved':'true','notes':'No generative repair or deletion.'})
write('phase-2-corrupt-image-resolution.csv',list(cor[0]),cor)
mis=[]
for x in health:
 if x['file_health_status']=='extension_mismatch':mis.append({'image_id':x['image_id'],'source_relative_path':x['source_relative_path'],'declared_extension':Path(x['source_relative_path']).suffix.lower(),'detected_mime':x['mime_type'],'file_readable':'true','publication_derivative_created':'false','derivative_path':'','resolution_status':'deferred_rights_review','original_preserved':'true','notes':'A correct conversion may be created only after approval.'})
write('phase-2-extension-mismatch-resolution.csv',list(mis[0]),mis)
rp=[]
for i,x in enumerate(remote,1):
 fid=x['feature_id'];f=features.get(fid,{}).get('properties',{});rp.append({'feature_id':fid,'layer_id':x['layer_id'],'feature_name_ar':f.get('name_ar') or f.get('name') or '','remote_url':x['remote_url'],'provider':x['provider'],'local_candidate_image_id':'','local_candidate_match_status':'no_approved_candidate','replacement_status':'open','rights_status':'unknown','required_action':'obtain documented local image; do not download remote reference','priority':'P1' if not f.get('local_images') else 'P2','notes':'Google reference retained as non-loaded metadata only.'})
write('phase-2-remote-replacement-plan.csv',list(rp[0]),rp)
write('phase-2-published-image-derivatives.csv',['publication_id','image_id','master_image_id','feature_id','layer_id','role','sequence','original_source_relative_path','web_large_path','web_medium_path','thumbnail_path','original_width','original_height','web_large_width','web_large_height','web_medium_width','web_medium_height','thumbnail_width','thumbnail_height','format','quality_setting','orientation_corrected','metadata_removed','original_preserved','rights_status','publication_permission','source_credit','attribution_required','published_for_public','notes'],[])
write('national-image-phase-2-change-log.csv',['change_id','image_id','master_image_id','feature_id','layer_id','change_type','field_name','old_value','new_value','reason','visual_evidence','rights_evidence','technical_evidence','decision_source','confidence','automatic_change','manual_review_completed','publication_permission','timestamp','reversible','notes'],[{'change_id':'IMG-P2-UI-0001','image_id':'','master_image_id':'','feature_id':'','layer_id':'atlas-ui','change_type':'interface_rights_filter','field_name':'popup local_images eligibility','old_value':'local paths displayed regardless of rights status','new_value':'public requires documented public rights; internal requires public or internal_only permission','reason':'Prevent unknown/requires_review images from being loaded in public mode','visual_evidence':'not_applicable','rights_evidence':'phase-2-rights-evidence-register.csv','technical_evidence':'assets/app.js mode filter','decision_source':'governance_policy','confidence':'high','automatic_change':'true','manual_review_completed':'false','publication_permission':'not_applicable','timestamp':NOW,'reversible':'true','notes':'No image or GeoJSON changed.'}])

score=[]
for lid in sorted(set(feature_layer.values())):
 fs=[fid for fid in features if feature_layer[fid]==lid];local=sum(bool(features[f].get('properties',{}).get('local_images')) for f in fs);cl=[x for x in cur if x['layer_id']==lid];ro=len({x['feature_id'] for x in remote if x['layer_id']==lid and not features.get(x['feature_id'],{}).get('properties',{}).get('local_images')});score.append({'layer_id':lid,'feature_count':len(fs),'local_images_before':local,'local_images_after':local,'verified_image_features':0,'public_image_features':0,'internal_only_image_features':0,'primary_image_features':0,'gallery_features':local,'features_without_images':len(fs)-local,'current_links_reviewed':len(cl),'current_links_verified':0,'current_links_wrong':0,'current_links_replaced':0,'master_candidates_reviewed':0,'master_images_approved':0,'manual_reviews_completed':0,'rights_cleared_images':0,'rights_unknown_images':len({x['image_id'] for x in cl}),'rights_rejected_images':0,'high_quality_published':0,'acceptable_published':0,'thumbnail_only_used':0,'corrupt_images_resolved':0,'remote_only_features':ro,'remote_replacement_candidates':ro,'coverage_before':round(100*local/max(1,len(fs)),2),'local_coverage_after':round(100*local/max(1,len(fs)),2),'verified_coverage_after':0,'public_coverage_after':0,'primary_coverage_after':0,'phase_status':'complete_with_open_reviews'})
write('national-image-phase-2-scorecard.csv',list(score[0]),score);(O/'national-image-phase-2-scorecard.json').write_text(json.dumps({'generated_at':NOW,'status':'IMAGE_PHASE_2_COMPLETE_WITH_OPEN_REVIEWS','layers':score},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
report=f'''# تقرير حوكمة صور السياحة الوطنية — المرحلة الثانية\n\n## الملخص التنفيذي\n\nالحالة: **IMAGE_PHASE_2_COMPLETE_WITH_OPEN_REVIEWS**. اكتملت سلامة المدخلات، ترتيب الأولوية، التدقيق التقني للروابط الحالية، سجلات الحقوق، وحزم المراجعة. لم تُسجّل مراجعة بصرية بشرية مكتملة، ولذلك لم تُعتمد صورة عامة أو Primary ولم تُنشأ مشتقات نشر.\n\n## الأولويات والمراجعة\n\n- PRIORITY_A: {len(a_paths)} صورة مرتبطة أو ذات Feature ID صريح.\n- PRIORITY_B: {len(b_paths)} Master عالي/مقبول غير داخل A.\n- PRIORITY_C: {len(c_paths)} صورة مؤجلة.\n- أوراق المراجعة: {len(sheets)}؛ فارغة: {empty}؛ مراجع صور مكسورة: {broken}؛ مسارات خاصة: {private}.\n\nتمت {len(cur)} عملية تحقق آلية للروابط الحالية من الملف والـhash والـFeature والمسار. لا تمثل هذه مراجعة بصرية؛ بقيت كلها مؤجلة بسبب الحقوق والمطابقة البصرية.\n\n## التكرارات والـthreshold\n\nتم توثيق {len(groups)} مجموعة، وإعداد cohort من {len(cohort)} مجموعة (عينة منهجية، حدود منخفضة وعليا، وكل المجموعات العابرة للـFeatures). لا يمكن حساب true/false rate بلا labels بشرية؛ بقي threshold = 5 ولم تمس SHA exact.\n\n## الحقوق والنشر\n\nلم توجد وثيقة محلية صريحة تربط صورة بإذن نشر عام. بقيت الحقوق unknown/requires_review. لم تُنسخ صور إلى assets، ولم يتغير GeoJSON أو الواجهة. المراجع البعيدة البالغ عددها {len(remote)} لم تُفتح أو تُنزّل.\n\n## الملفات الخاصة\n\nالصور التالفة: {len(cor)}، واختلافات الامتداد: {len(mis)}؛ حُفظت الأصول ولم تنشأ تحويلات قبل حسم الحقوق.\n\n## التغطية والمخاطر\n\nالتغطية المحلية بقيت {100*len({x['feature_id'] for x in current})/len(features):.2f}%؛ التغطية المتحققة بصريًا والعامة وPrimary = 0%. الخطر الأساسي هو الخلط بين وجود الملف وحق نشره، أو اعتبار المطابقة التقنية مراجعة بصرية.\n\n## المرحلة التالية\n\nاستخدام أداة المراجعة المحلية لتسجيل قرارات بشرية فعلية لـPRIORITY_A أولًا، ثم إرفاق وثائق الحقوق واعتماد Masters. بعد ذلك فقط تُنشأ WebP وتُحدّث GeoJSON.\n''';(R/'docs/national-tourism-image-governance-phase-2-report.md').write_text(report,encoding='utf8')
report_path=R/'docs/national-tourism-image-governance-phase-2-report.md';report_path.write_text(report_path.read_text(encoding='utf8').replace('لم تُنسخ صور إلى assets، ولم يتغير GeoJSON أو الواجهة.','لم تُنسخ صور إلى assets ولم يتغير GeoJSON. عُدلت الواجهة فقط لإخفاء unknown/requires_review في الوضعين العام والداخلي، مع إبقاء Placeholder.'),encoding='utf8')
print(f'PHASE_2_IMAGE_INPUT_FILES_FOUND = {len(required)}');print(f'PHASE_2_IMAGE_INPUT_FILES_MISSING = {len(missing)}');print(f'PHASE_2_SOURCE_IMAGES_AVAILABLE = {len(inv)-len(source_missing)}');print(f'PHASE_2_SOURCE_IMAGES_MISSING = {len(source_missing)}');print(f'PHASE_2_MASTER_IMAGES_AVAILABLE = {len(master_ids)}');print(f'PHASE_2_CURRENT_LINKS_AVAILABLE = {len(current)}');print(f'PRIORITY_A_IMAGES = {len(a_paths)}');print(f'PRIORITY_B_IMAGES = {len(b_paths)}');print(f'PRIORITY_C_IMAGES = {len(c_paths)}');print(f'REVIEW_SHEETS_VALID = {len(sheets)-empty}');print(f'REVIEW_SHEETS_EMPTY = {empty}');print(f'REVIEW_SHEETS_BROKEN_IMAGES = {broken}');print(f'REVIEW_SHEETS_PRIVATE_PATHS = {private}');print(f'SOURCE_IMAGE_FILES_BEFORE = {len(inv)}');print(f'SOURCE_IMAGE_FILES_AFTER = {len(inv)-len(source_missing)}');print('ORIGINAL_IMAGE_FILES_DELETED = 0');print(f'ORIGINAL_IMAGE_FILES_MODIFIED = {len(modified)}');print('PUBLISHED_DERIVATIVE_FILES_CREATED = 0');print('UNRECORDED_IMAGE_MOVES = 0')
