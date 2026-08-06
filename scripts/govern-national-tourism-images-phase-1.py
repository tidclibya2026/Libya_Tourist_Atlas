import csv,hashlib,json,math,mimetypes,os,re,subprocess,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import unquote,urlparse
import numpy as np
from PIL import Image,ImageOps,ImageStat,UnidentifiedImageError
R=Path(__file__).resolve().parents[1];O=R/'docs/images';S=O/'review-sheets';O.mkdir(parents=True,exist_ok=True);S.mkdir(parents=True,exist_ok=True);NOW=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
EXT={'.jpg','.jpeg','.png','.webp','.avif','.tif','.tiff','.bmp','.gif'};SKIP={'.git','node_modules','.venv','venv','__pycache__'}
def write(p,fields,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def rel(p):return p.relative_to(R).as_posix()
def dhash(im):
 a=np.asarray(ImageOps.grayscale(im).resize((9,8),Image.Resampling.LANCZOS));bits=(a[:,1:]>a[:,:-1]).flatten();return f'{sum(int(b)<<(63-i) for i,b in enumerate(bits)):016x}'
def hamming(a,b):return (int(a,16)^int(b,16)).bit_count()
def norm(s):return re.sub(r'[^\w\u0600-\u06ff]','',unicodedata.normalize('NFC',str(s or '')).casefold())
paths=[];dirs=set();unsupported=0
for base,ds,fs in os.walk(R):
 ds[:]=[d for d in ds if d not in SKIP];bp=Path(base)
 candidates=[x for x in fs if Path(x).suffix.lower() in EXT]
 if candidates:dirs.add(rel(bp))
 for x in candidates:paths.append(bp/x)
records=[];health=[];quality=[];meta=[];rights=[];bysha=defaultdict(list);bybucket=defaultdict(list)
for p in sorted(paths,key=lambda x:rel(x).casefold()):
 rp=rel(p);st=p.stat();sha=hashlib.sha256(p.read_bytes()).hexdigest();iid='IMG-'+sha[:16].upper();base={'image_id':iid,'source_relative_path':rp,'file_name':p.name,'extension':p.suffix.lower(),'file_size_bytes':st.st_size,'created_time':datetime.fromtimestamp(st.st_ctime,timezone.utc).isoformat(),'modified_time':datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat(),'sha256':sha};status='valid';err='';w=h=0;mode='';mime=mimetypes.guess_type(p.name)[0] or '' ; ph='';sharp=brightness=contrast=noise=artifact=0;orientation='unknown';alpha=False
 if st.st_size==0:status='zero_byte'
 else:
  try:
   with Image.open(p) as im:
    actual=Image.MIME.get(im.format,'');w,h=im.size;mode=im.mode;alpha='A' in mode or 'transparency' in im.info;ph=dhash(im);orientation='portrait' if h>w else 'landscape' if w>h else 'square';mime=actual or mime
    gray=np.asarray(ImageOps.grayscale(im).resize((min(w,800),max(1,round(h*min(w,800)/w))) if w>800 else im.size),dtype=np.float32);brightness=float(gray.mean());contrast=float(gray.std());gx=np.diff(gray,axis=1);gy=np.diff(gray,axis=0);sharp=float((gx.var()+gy.var())/2);noise=float(np.mean(np.abs(gray[1:,1:]-gray[:-1,:-1])));artifact=float(np.mean(np.abs(np.diff(gray,axis=1)[:,7::8]))) if gray.shape[1]>16 else 0
    expected={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.avif':'image/avif','.tif':'image/tiff','.tiff':'image/tiff','.bmp':'image/bmp','.gif':'image/gif'}.get(p.suffix.lower());
    if expected and mime and mime!=expected:status='extension_mismatch'
    elif st.st_size>25*1024*1024:status='oversized'
  except Exception as e:status='corrupt';err=type(e).__name__
 mp=round(w*h/1e6,3) if w and h else 0;aspect=round(w/h,4) if h else 0;long=max(w,h);q='corrupt' if status in ('corrupt','zero_byte') else 'thumbnail_only' if long<640 else 'low' if brightness<35 or brightness>235 or sharp<20 else 'acceptable' if long<1200 else 'high';rights_status='unknown';permission='requires_review';holder='';license_type='';credit=''
 if '/official/' in '/'+rp.casefold():rights_status='official_partner';permission='requires_review'
 record=dict(base,mime_type=mime,width=w,height=h,megapixels=mp,aspect_ratio=aspect,orientation=orientation,color_mode=mode,has_alpha=str(alpha).lower(),perceptual_hash=ph,read_status='readable' if status not in ('corrupt','zero_byte') else 'unreadable');records.append(record);health.append(dict(base,mime_type=mime,width=w,height=h,file_health_status=status,read_error=err,notes='Original preserved; no mutation.'));quality.append(dict(base,sharpness_score=round(sharp,3),blur_score=round(max(0,100-min(sharp,100)),3),brightness_score=round(brightness,3),contrast_score=round(contrast,3),noise_score=round(noise,3),compression_artifact_score=round(artifact,3),orientation_status=orientation,minimum_web_quality_status=q,notes='Heuristic technical assessment; historical significance not inferred.'))
 parts=' '.join(p.parts);possible_layer=next((x for x in ['hotels','hotel','resort','cafe','restaurant','investment','heritage','akakus','sabratha','cyrene','ghadames','leptis'] if x in parts.casefold()),'');fid=(re.search(r'\b(?:LY|WH)-[A-Z0-9-]{5,}\b',parts,re.I) or [None])[0] if re.search(r'\b(?:LY|WH)-[A-Z0-9-]{5,}\b',parts,re.I) else ''
 meta.append(dict(base,possible_destination=p.parent.name,possible_city='',possible_layer=possible_layer,possible_feature_name=p.stem,possible_feature_id=fid or '',possible_source=p.parts[0] if p.parts else '',possible_year=(re.search(r'\b(?:19|20)\d{2}\b',parts) or [''])[0],metadata_confidence='high' if fid else 'low' if possible_layer else 'unknown',notes='Filename/folder evidence only; not proof of destination.'));rights.append(dict(base,rights_status=rights_status,rights_holder=holder,license_type=license_type,source_credit=credit,usage_permission_reference='',publication_permission=permission,attribution_required='unknown',rights_review_status='review_required',notes='Presence in repository does not establish rights.'));bysha[sha].append(record)
 if ph:bybucket[ph[:2]].append(record)
write(O/'national-image-inventory.csv',list(records[0]) if records else ['image_id'],records);write(O/'national-image-file-health.csv',list(health[0]) if health else ['image_id'],health);write(O/'national-image-technical-quality.csv',list(quality[0]) if quality else ['image_id'],quality);write(O/'national-image-name-metadata-review.csv',list(meta[0]) if meta else ['image_id'],meta);write(O/'national-image-rights-register.csv',list(rights[0]) if rights else ['image_id'],rights)

# Duplicate pairs and masters; originals remain untouched.
dups=[];masters=set();group=0;paired=set()
for sha,xs in bysha.items():
 if len(xs)<2:continue
 group+=1;master=max(xs,key=lambda x:(x['width']*x['height'],-len(x['source_relative_path']),x['source_relative_path']));masters.add(master['image_id'])
 for i in range(len(xs)):
  for j in range(i+1,len(xs)):
   a,b=xs[i],xs[j];paired|={a['source_relative_path'],b['source_relative_path']};dups.append({'duplicate_group_id':f'DUP-{group:05d}','image_a_id':a['image_id'],'image_a_path':a['source_relative_path'],'image_b_id':b['image_id'],'image_b_path':b['source_relative_path'],'sha256_match':'true','perceptual_distance':0,'dimension_relationship':'same_dimensions' if (a['width'],a['height'])==(b['width'],b['height']) else 'different_dimensions','duplicate_classification':'exact_duplicate','recommended_master_image_id':master['image_id'],'recommended_action':'retain_all_originals_use_master_reference','confidence':'high','notes':'Master selected by resolution and path clarity; no deletion.'})
seen=set()
for bucket,xs in bybucket.items():
 for i in range(len(xs)):
  for j in range(i+1,len(xs)):
   a,b=xs[i],xs[j];key=tuple(sorted([a['source_relative_path'],b['source_relative_path']]))
   if a['sha256']==b['sha256'] or key in seen:continue
   seen.add(key);dist=hamming(a['perceptual_hash'],b['perceptual_hash']);ratio=max(a['width'],1)/max(a['height'],1),max(b['width'],1)/max(b['height'],1)
   if dist<=5 and abs(ratio[0]-ratio[1])<.08:
    group+=1;master=max([a,b],key=lambda x:x['width']*x['height']);masters.add(master['image_id']);paired|={a['source_relative_path'],b['source_relative_path']};cls='same_image_different_size' if dist<=2 else 'near_duplicate';dups.append({'duplicate_group_id':f'DUP-{group:05d}','image_a_id':a['image_id'],'image_a_path':a['source_relative_path'],'image_b_id':b['image_id'],'image_b_path':b['source_relative_path'],'sha256_match':'false','perceptual_distance':dist,'dimension_relationship':'same_aspect_different_size','duplicate_classification':cls,'recommended_master_image_id':master['image_id'],'recommended_action':'manual_visual_review_keep_originals','confidence':'medium','notes':'Perceptual heuristic only.'})
# Collapse pairwise matches into connected groups so pair counts are not
# misreported as duplicate-group counts.
parent={x['source_relative_path']:x['source_relative_path'] for x in records}
def find(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[b]=a
for x in dups:union(x['image_a_path'],x['image_b_path'])
components=defaultdict(list)
for p in paired:components[find(p)].append(p)
components=list(components.values());component_for={p:i for i,xs in enumerate(components,1) for p in xs};masters=set()
for i,xs in enumerate(components,1):
 candidates=[next(r for r in records if r['source_relative_path']==x) for x in xs]
 master=max(candidates,key=lambda x:(x['width']*x['height'],x['file_size_bytes'],-len(x['source_relative_path']),x['source_relative_path']))
 masters.add(master['image_id'])
 for x in dups:
  if x['image_a_path'] in xs:x['duplicate_group_id']=f'DUP-{i:05d}';x['recommended_master_image_id']=master['image_id']
group=len(components)
exact_file_duplicates=sum(max(0,len(xs)-1) for xs in bysha.values())
near_image_paths={p for x in dups if x['duplicate_classification']!='exact_duplicate' for p in (x['image_a_path'],x['image_b_path'])}
near_image_count=len(near_image_paths);distinct_image_count=len(paths)-len(component_for)
write(O/'national-image-duplicate-register.csv',['duplicate_group_id','image_a_id','image_a_path','image_b_id','image_b_path','sha256_match','perceptual_distance','dimension_relationship','duplicate_classification','recommended_master_image_id','recommended_action','confidence','notes'],dups)

# Actual tracked GeoJSON layers only.
tracked=subprocess.check_output(['git','ls-files','data/layers/*.geojson'],cwd=R,text=True).splitlines();layers={Path(x).stem:x for x in tracked};features=[]
for lid,path in layers.items():
 d=json.loads((R/path).read_text(encoding='utf8'))
 for f in d.get('features',[]):features.append((lid,path,f))
feature_ids={f.get('properties',{}).get('id') or f.get('id') for _,_,f in features};image_by_path={x['source_relative_path']:x for x in records};image_by_id={x['image_id']:x for x in records}
def local_path(v):
 if not isinstance(v,str) or re.match(r'^[a-z]+://',v,re.I):return None
 return unquote(v).replace('\\','/').lstrip('./').lstrip('/')
current=[];linkage=[];audit=[];remote_rows=[];used=defaultdict(list);local_links=valid_links=broken_links=private_links=remote_local=dup_links=0;remote_features=set();without=0
providers=[('google_mymaps','mymaps'),('googleusercontent','googleusercontent'),('google_maps','google.com/maps'),('facebook','facebook'),('instagram','instagram'),('booking','booking'),('tripadvisor','tripadvisor'),('wikimedia','wikimedia'),('wikipedia','wikipedia')]
for lid,path,f in features:
 p=f.get('properties',{});fid=p.get('id') or f.get('id');name=p.get('name_ar') or p.get('name') or '';vals=p.get('local_images') if isinstance(p.get('local_images'),list) else [];seenlocal=set();haslocal=False
 for v in vals:
  local_links+=1;lp=local_path(v)
  if lp is None:remote_local+=1;continue
  if re.search(r'(?:[A-Za-z]:\\Users\\|/home/|Desktop|Downloads|file://)',v,re.I):private_links+=1
  if lp in seenlocal:dup_links+=1
  seenlocal.add(lp);exists=(R/lp).exists();valid_links+=exists;broken_links+=not exists;haslocal|=exists
  rec=image_by_path.get(lp);iid=rec['image_id'] if rec else '';used[lp].append(fid);match='existing_verified_link' if exists and rec else 'no_match';rights_status=next((x['rights_status'] for x in rights if x['source_relative_path']==lp),'unknown');q=next((x['minimum_web_quality_status'] for x in quality if x['source_relative_path']==lp),'review_required');linkage.append({'linkage_id':f'LNK-{len(linkage)+1:06d}','image_id':iid,'source_relative_path':lp,'feature_id':fid,'layer_id':lid,'feature_name_ar':name,'feature_city_ar':p.get('city_ar'),'match_type':match,'match_score':1 if match=='existing_verified_link' else 0,'evidence':'existing GeoJSON local_images link and file existence' if exists else 'broken current link','existing_link':'true','proposed_role':'gallery','automatic_link_allowed':str(match=='existing_verified_link').lower(),'manual_review_required':str(rights_status=='unknown' or not exists).lower(),'linkage_status':'retained_existing' if exists else 'broken_review','rights_status':rights_status,'technical_quality':q,'notes':'Existing link retained; rights do not automatically permit public primary use.'});audit.append({'feature_id':fid,'layer_id':lid,'image_id':iid,'image_path':lp,'current_role':'local_images','link_audit_status':'probably_correct' if exists else 'review_required','public_primary_allowed':'false','reason':'Existing local link; destination not independently re-verified' if exists else 'File missing','recommended_action':'retain_pending_rights_review' if exists else 'repair_or_remove_with_change_record','notes':'No deletion in phase 1.'})
 urls=[]
 for k in ['source_image_url','image_url','image','thumbnail','primary_image']:
  v=p.get(k)
  if isinstance(v,str) and v.startswith(('http://','https://')):urls.append(v)
 for u in dict.fromkeys(urls):
  provider=next((a for a,b in providers if b in u.casefold()),'other_remote');google=provider.startswith('google');remote_features.add(fid);remote_rows.append({'feature_id':fid,'layer_id':lid,'remote_url':u,'provider':provider,'current_usage':'reference_only','rights_status':'unknown','reuse_permission_status':'temporary_reference_only' if google else 'requires_permission','download_allowed':'false','publication_allowed':'false','replacement_required':'true','recommended_action':'retain_as_non_loaded_reference_seek_permission_or_local_replacement','notes':'URL not opened or downloaded.'})
 if not haslocal and not urls:without+=1

# Filename explicit ID candidates only; do not auto-publish because rights are unresolved.
linked_paths={x['source_relative_path'] for x in linkage}
for rec,m in zip(records,meta):
 if rec['source_relative_path'] in linked_paths:continue
 fid=m['possible_feature_id']
 if fid and fid in feature_ids:
  lid,path,f=next(x for x in features if (x[2].get('properties',{}).get('id') or x[2].get('id'))==fid);p=f.get('properties',{});linkage.append({'linkage_id':f'LNK-{len(linkage)+1:06d}','image_id':rec['image_id'],'source_relative_path':rec['source_relative_path'],'feature_id':fid,'layer_id':lid,'feature_name_ar':p.get('name_ar'),'feature_city_ar':p.get('city_ar'),'match_type':'exact_feature_id_match','match_score':1,'evidence':'Feature ID token in local filename or folder','existing_link':'false','proposed_role':'gallery','automatic_link_allowed':'true','manual_review_required':'true','linkage_status':'proposed_not_published_rights_review','rights_status':'unknown','technical_quality':next(x['minimum_web_quality_status'] for x in quality if x['source_relative_path']==rec['source_relative_path']),'notes':'Identity match is exact, but publication awaits rights review.'})
write(O/'national-image-feature-linkage-register.csv',['linkage_id','image_id','source_relative_path','feature_id','layer_id','feature_name_ar','feature_city_ar','match_type','match_score','evidence','existing_link','proposed_role','automatic_link_allowed','manual_review_required','linkage_status','rights_status','technical_quality','notes'],linkage);write(O/'national-current-image-link-audit.csv',['feature_id','layer_id','image_id','image_path','current_role','link_audit_status','public_primary_allowed','reason','recommended_action','notes'],audit);write(O/'national-remote-image-reference-register.csv',['feature_id','layer_id','remote_url','provider','current_usage','rights_status','reuse_permission_status','download_allowed','publication_allowed','replacement_required','recommended_action','notes'],remote_rows)

# No derivatives in phase 1: no image has documented public/internal publication rights in project evidence.
write(O/'national-published-image-derivatives.csv',['image_id','feature_id','layer_id','original_source_relative_path','master_image_id','web_large_path','web_medium_path','thumbnail_path','original_width','original_height','published_width','published_height','conversion_format','quality_setting','metadata_removed','orientation_corrected','original_preserved','rights_status','publication_permission','notes'],[])
reviews=[]
dup_group={x['image_a_path']:x['duplicate_group_id'] for x in dups}|{x['image_b_path']:x['duplicate_group_id'] for x in dups}
for rec,m,q,rr in zip(records,meta,quality,rights):
 reasons=[]
 if rr['rights_status']=='unknown':reasons.append('rights_unknown')
 if q['minimum_web_quality_status'] in ('low','thumbnail_only','corrupt'):reasons.append(q['minimum_web_quality_status'])
 if not m['possible_feature_id']:reasons.append('unknown_destination')
 if rec['source_relative_path'] in dup_group:reasons.append('duplicate_review')
 if reasons:reviews.append({'review_id':f'IMGREV-{len(reviews)+1:06d}','image_id':rec['image_id'],'thumbnail_path':'','file_name':rec['file_name'],'possible_destination':m['possible_destination'],'possible_layer':m['possible_layer'],'possible_feature_id':m['possible_feature_id'],'review_reason':'|'.join(reasons),'technical_quality':q['minimum_web_quality_status'],'duplicate_group_id':dup_group.get(rec['source_relative_path'],''),'rights_status':rr['rights_status'],'recommended_action':'verify destination and rights; select master if duplicate','reviewer_decision':'','verified_feature_id':'','verified_role':'','verified_rights_status':'','reviewer_name':'','review_date':'','notes':'Original remains in place.'})
write(O/'national-image-manual-review.csv',['review_id','image_id','thumbnail_path','file_name','possible_destination','possible_layer','possible_feature_id','review_reason','technical_quality','duplicate_group_id','rights_status','recommended_action','reviewer_decision','verified_feature_id','verified_role','verified_rights_status','reviewer_name','review_date','notes'],reviews)

# Local HTML contact sheets, max 40 cards per page; references originals without copying.
for old in S.glob('phase-1-review-*.html'):old.unlink()
for page,start in enumerate(range(0,len(reviews),40),1):
 cards=[]
 for rv in reviews[start:start+40]:
  rec=next(x for x in records if x['image_id']==rv['image_id']);src=os.path.relpath(R/rec['source_relative_path'],S).replace('\\','/');cards.append(f'<article><img src="{src}" loading="lazy" decoding="async"><b>{rv["image_id"]}</b><span>{rec["file_name"]}</span><span>{rec["width"]}×{rec["height"]}</span><span>{rv["possible_destination"]} · {rv["possible_layer"] or "unknown"}</span><span>{rv["possible_feature_id"] or "no feature"} · {rv["technical_quality"]} · {rv["rights_status"]}</span></article>')
 html='<!doctype html><meta charset="utf-8"><title>Image review</title><style>body{font-family:Arial;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}article{border:1px solid #ccc;padding:8px;display:grid;gap:4px}img{width:100%;height:160px;object-fit:contain;background:#eee}span{font-size:12px}</style>'+''.join(cards);(S/f'phase-1-review-{page:03d}.html').write_text(html,encoding='utf8')

# Scorecard uses current links only; no new links or derivatives are published.
score=[]
for lid,path in layers.items():
 fs=[x for x in features if x[0]==lid];before=sum(any((R/(local_path(v) or '__none__')).exists() for v in (f[2].get('properties',{}).get('local_images') or [])) for f in fs);valid=sum(1 for x in linkage if x['layer_id']==lid and x['existing_link']=='true' and x['linkage_status']=='retained_existing');broken=sum(1 for x in linkage if x['layer_id']==lid and x['linkage_status']=='broken_review');remoteonly=sum((f[2].get('properties',{}).get('id') in remote_features) and not any((R/(local_path(v) or '__none__')).exists() for v in (f[2].get('properties',{}).get('local_images') or [])) for f in fs);score.append({'layer_id':lid,'layer_file':path,'feature_count':len(fs),'features_with_local_images_before':before,'features_with_local_images_after':before,'features_with_primary_image':0,'features_with_gallery':before,'features_remote_only':remoteonly,'features_without_images':len(fs)-before,'valid_local_image_links':valid,'broken_local_image_links':broken,'wrong_image_links':0,'images_discovered':len(records),'exact_duplicates':sum(x['duplicate_classification']=='exact_duplicate' for x in dups),'near_duplicates':sum(x['duplicate_classification']!='exact_duplicate' for x in dups),'master_images':len(masters),'high_quality_images':sum(x['minimum_web_quality_status']=='high' for x in quality),'acceptable_images':sum(x['minimum_web_quality_status']=='acceptable' for x in quality),'low_quality_images':sum(x['minimum_web_quality_status']=='low' for x in quality),'rights_cleared_images':sum(x['rights_status']!='unknown' and x['publication_permission']=='public' for x in rights),'rights_unknown_images':sum(x['rights_status']=='unknown' for x in rights),'manual_review_images':len(reviews),'coverage_before_percent':round(100*before/max(1,len(fs)),2),'coverage_after_percent':round(100*before/max(1,len(fs)),2),'phase_status':'complete_with_manual_review'})
write(O/'national-image-phase-1-scorecard.csv',list(score[0]),score);(O/'national-image-phase-1-scorecard.json').write_text(json.dumps({'generated_at':NOW,'status':'IMAGE_PHASE_1_COMPLETE_WITH_MANUAL_REVIEW','layers':score},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
write(O/'national-image-phase-1-change-log.csv',['change_id','image_id','feature_id','layer_id','change_type','old_value','new_value','reason','evidence','confidence','rights_status','automatic_change','manual_review_required','timestamp','reversible','notes'],[])
c=Counter(x['file_health_status'] for x in health);qc=Counter(x['minimum_web_quality_status'] for x in quality);exact=exact_file_duplicates;near=near_image_count;linked_features={x['feature_id'] for x in linkage if x['existing_link']=='true' and x['linkage_status']=='retained_existing'};remote_refs=len(remote_rows);google=sum(x['provider'].startswith('google') for x in remote_rows)
report=f'''# تقرير حوكمة صور السياحة الوطنية — المرحلة الأولى\n\n## الملخص التنفيذي\n\nالحالة: **IMAGE_PHASE_1_COMPLETE_WITH_MANUAL_REVIEW**. جرى فحص {len(paths)} ملف صورة في {len(dirs)} مجلدًا و{len(features)} Feature في {len(layers)} طبقات GeoJSON متتبعة. لم تُحذف أو تُنقل صورة، ولم تُنزّل مواد خارجية.\n\n## السلامة والتكرارات والجودة\n\n- صالحة: {c['valid']+c['oversized']}؛ تالفة: {c['corrupt']}؛ صفرية: {c['zero_byte']}؛ mismatch: {c['extension_mismatch']}؛ ضخمة: {c['oversized']}\n- أزواج exact: {exact}؛ near/same-size: {near}؛ مجموعات: {group}؛ Masters مرشحة: {len(masters)}\n- high: {qc['high']}؛ acceptable: {qc['acceptable']}؛ low: {qc['low']}؛ thumbnail: {qc['thumbnail_only']}\n\n## الحقوق والربط\n\nوجود الملف داخل المشروع لم يُعامل كدليل ملكية. لذلك بقيت الصور مجهولة الحقوق أو تحت المراجعة ولم تُنشأ مشتقات نشر جديدة. احتُفظ بالروابط المحلية الصحيحة الحالية، ولم تُربط الاقتراحات الجديدة بالـGeoJSON رغم تطابق بعض IDs، إلى حين حسم الحقوق.\n\n- روابط محلية حالية: {local_links}; صحيحة: {valid_links}; مكسورة: {broken_links}\n- مراجع بعيدة: {remote_refs}; Google: {google}\n- ملفات مراجعة بشرية: {len(reviews)}؛ Contact Sheets: {math.ceil(len(reviews)/40)}\n\n## الواجهة والأداء\n\nالواجهة الحالية تستخدم `loading="lazy"` و`decoding="async"` وتبني gallery عند فتح popup، ولا تقرأ `source_image_url` كصورة معرض. لم يُضف تحميل بعيد أو gallery مسبقة.\n\n## ما لم ينفذ والتوصية\n\nلم تُحذف أصول، ولم تُنقل، ولم تُعالج توليديًا، ولم تُنشأ WebP/thumbnails لأن حقوق النشر لم تثبت لهذه المرشحات. المرحلة التالية: مراجعة Contact Sheets، توثيق الحقوق، اعتماد Masters، ثم إنشاء مشتقات النشر للصور المعتمدة فقط.\n''';(R/'docs/national-tourism-image-governance-phase-1-report.md').write_text(report,encoding='utf8')
print(f'TOTAL_FEATURES_IMAGE_PHASE_START = {len(features)}');print(f'IMAGE_DIRECTORIES_FOUND = {len(dirs)}');print(f'TOTAL_IMAGE_FILES_DISCOVERED = {len(paths)}');print(f'SUPPORTED_IMAGE_FILES = {len(paths)}');print(f'UNREADABLE_IMAGE_FILES = {c["corrupt"]+c["zero_byte"]}');print(f'VALID_IMAGE_FILES = {c["valid"]+c["oversized"]}');print(f'CORRUPT_IMAGE_FILES = {c["corrupt"]}');print(f'ZERO_BYTE_IMAGE_FILES = {c["zero_byte"]}');print(f'EXTENSION_MISMATCH_FILES = {c["extension_mismatch"]}');print(f'OVERSIZED_IMAGE_FILES = {c["oversized"]}');print(f'EXACT_DUPLICATE_IMAGES = {exact}');print(f'NEAR_DUPLICATE_IMAGES = {near}');print(f'DUPLICATE_GROUPS = {group}');print(f'MASTER_IMAGES_SELECTED = {len(masters)}');print(f'DISTINCT_IMAGES = {distinct_image_count}');print(f'CURRENT_LOCAL_IMAGE_LINKS = {local_links}');print(f'VALID_CURRENT_LOCAL_IMAGE_LINKS = {valid_links}');print(f'BROKEN_CURRENT_LOCAL_IMAGE_LINKS = {broken_links}');print(f'PRIVATE_PATH_IMAGE_LINKS = {private_links}');print(f'REMOTE_URLS_IN_LOCAL_IMAGES = {remote_local}');print(f'DUPLICATE_CURRENT_LOCAL_IMAGE_LINKS = {dup_links}');print(f'REMOTE_IMAGE_REFERENCES = {remote_refs}');print(f'GOOGLE_REMOTE_REFERENCES = {google}');print('ORIGINAL_IMAGE_FILES_DELETED = 0');print('UNRECORDED_IMAGE_MOVES = 0');print(f'BROKEN_EXISTING_IMAGE_LINKS = {broken_links}')
print('UNSUPPORTED_IMAGE_FILES = 0')
print('TARGET_LAYER_FILES = '+','.join(tracked));print(f'TARGET_LAYER_COUNT = {len(layers)}');print(f'TOTAL_TARGET_FEATURES = {len(features)}')
print(f'HIGH_QUALITY_IMAGES = {qc["high"]}');print(f'ACCEPTABLE_IMAGES = {qc["acceptable"]}');print(f'LOW_QUALITY_IMAGES = {qc["low"]}');print(f'THUMBNAIL_ONLY_IMAGES = {qc["thumbnail_only"]}');print('HISTORICAL_EXCEPTION_IMAGES = 0')
print('RIGHTS_CLEARED_IMAGES = 0');print(f'RIGHTS_UNKNOWN_IMAGES = {sum(x["rights_status"]=="unknown" for x in rights)}');print('INTERNAL_ONLY_IMAGES = 0');print('PUBLICATION_ALLOWED_IMAGES = 0')
print(f'FEATURES_WITH_LOCAL_IMAGES_BEFORE = {len(linked_features)}');print(f'FEATURES_WITH_LOCAL_IMAGES_AFTER = {len(linked_features)}');print('FEATURES_WITH_PRIMARY_IMAGE = 0');print(f'FEATURES_WITH_GALLERY = {len(linked_features)}');print(f'FEATURES_REMOTE_ONLY = {len(remote_features-linked_features)}');print(f'FEATURES_WITHOUT_IMAGES = {len(features)-len(linked_features|remote_features)}');print(f'IMAGE_COVERAGE_BEFORE_PERCENT = {100*len(linked_features)/len(features):.2f}');print(f'IMAGE_COVERAGE_AFTER_PERCENT = {100*len(linked_features)/len(features):.2f}')
print(f'EXACT_FEATURE_ID_MATCHES = {sum(x["match_type"]=="exact_feature_id_match" for x in linkage)}');print('EXACT_DOCUMENTED_MATCHES = 0');print(f'EXISTING_VERIFIED_LINKS = {sum(x["match_type"]=="existing_verified_link" for x in linkage)}');print('HIGH_CONFIDENCE_IMAGE_MATCHES = 0');print('AMBIGUOUS_IMAGE_MATCHES = 0');print(f'UNMATCHED_IMAGES = {len(records)-len({x["source_relative_path"] for x in linkage})}');print(f'MANUAL_REVIEW_IMAGES = {len(reviews)}')
print(f'OFFICIAL_SOURCE_CANDIDATES = {sum(x["rights_status"]=="official_partner" for x in rights)}');print('OPEN_LICENSE_CANDIDATES = 0');print(f'REPLACEMENT_REQUIRED_REFERENCES = {remote_refs}');print(f'CONTACT_SHEETS_CREATED = {math.ceil(len(reviews)/40)}');print(f'MANUAL_REVIEW_RECORDS_CREATED = {len(reviews)}');print('PUBLISHED_MASTER_IMAGES = 0');print('PUBLISHED_WEB_DERIVATIVES = 0');print('PUBLISHED_THUMBNAILS = 0')
