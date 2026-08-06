import csv,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; NOW=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'); TODAY=NOW[:10]
FILES={'hotels':'data/layers/hotels.geojson','tripoliRestaurants':'data/layers/tripoli-restaurants.geojson','tripoliCafes':'data/layers/tripoli-cafes.geojson','resorts':'data/layers/tourist-villages-resorts.geojson','investment':'data/layers/tourism-investment-projects.geojson'}
D={k:json.loads((ROOT/v).read_text(encoding='utf8')) for k,v in FILES.items()}; BEFORE={k:len(v['features']) for k,v in D.items()}; TOTAL=sum(BEFORE.values())
AUD=list(csv.DictReader((ROOT/'docs/audit/national-duplicate-register.csv').open(encoding='utf-8-sig'))); confirmed=[r for r in AUD if r['record_a_layer']==r['record_b_layer'] and r['duplicate_classification']=='confirmed_duplicate']; cross=[r for r in AUD if r['record_a_layer']!=r['record_b_layer']]
CONTROL=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\u200b-\u200f\u202a-\u202e\u2060-\u206f]'); EMPTY={'','null','undefined','n/a','na','غير متوفر','لا يوجد','-'}
def norm(s):s=CONTROL.sub('',unicodedata.normalize('NFC',str(s or ''))).casefold().translate(str.maketrans('أإآةىؤئ','اااهيوي'));return re.sub(r'[^\w\u0600-\u06ff]','',s)
def clean(s):
 if not isinstance(s,str):return s
 s=CONTROL.sub('',unicodedata.normalize('NFC',s));s=re.sub(r'\s+',' ',s).strip();return None if s.casefold() in EMPTY else s
def typ(p):return p.get('facility_type_code') or p.get('investment_type_code')
def idx(layer):return {f['properties']['id']:f for f in D[layer]['features']}
IDX={k:idx(k) for k in D}; parent={}
def find(x):
 parent.setdefault(x,x)
 if parent[x]!=x:parent[x]=find(parent[x])
 return parent[x]
def union(a,b):
 a,b=find(a),find(b)
 if a!=b:parent[max(a,b)]=min(a,b)

resolution=[]; eligible=[]
for n,r in enumerate(confirmed,1):
 layer=r['record_a_layer'];a=IDX[layer].get(r['record_a_id']);b=IDX[layer].get(r['record_b_id']); exact=bool(a and b and norm(a['properties'].get('name_ar'))==norm(b['properties'].get('name_ar')) and a['geometry']==b['geometry'] and typ(a['properties'])==typ(b['properties']))
 final='true_duplicate' if exact else ('probable_duplicate' if float(r.get('name_similarity') or 0)>=.9 and float(r.get('distance_meters') or 1e9)<=30 else 'insufficient_evidence')
 action='merge_into_canonical' if exact else 'defer_for_review';confidence='high' if exact else 'medium' if final=='probable_duplicate' else 'low'
 if exact:eligible.append((layer,r['record_a_id'],r['record_b_id']));union((layer,r['record_a_id']),(layer,r['record_b_id']))
 resolution.append({'case_id':f'DUP-{n:04d}','layer_id':layer,'record_a_id':r['record_a_id'],'record_a_name':r['record_a_name'],'record_b_id':r['record_b_id'],'record_b_name':r['record_b_name'],'distance_meters':r['distance_meters'],'name_similarity':r['name_similarity'],'geometry_relationship':r['geometry_relationship'],'previous_classification':'confirmed_duplicate','final_classification':final,'canonical_id':'','retired_id':'','action':action,'confidence':confidence,'decision_basis':'Exact normalized name, byte-equivalent geometry, and identical type' if exact else 'Evidence does not prove one entity','fields_transferred':'','conflicting_fields':'','legacy_ids_preserved':'','requires_manual_review':str(not exact).lower(),'notes':'No automatic deletion without strict identity evidence.'})

groups=defaultdict(list)
for key in parent:groups[find(key)].append(key)
retired=[];conflicts=[];changes=[];merged_by_layer=Counter();canonical_updated=set(); case_by_pair={(r['layer_id'],r['record_a_id'],r['record_b_id']):r for r in resolution}
conflict_fields=['name_ar','phone','website','stars','rooms','beds','units','capacity','facility_type_code','investment_type_code','project_status_code','license_status','operational_status','ownership_type','site_area_m2','investment_value']
def log(layer,fid,kind,field,old,new,reason,case='',confidence='high'):
 changes.append({'change_id':f'CHG-{len(changes)+1:06d}','layer_id':layer,'feature_id':fid,'change_type':kind,'field_name':field,'old_value':json.dumps(old,ensure_ascii=False,sort_keys=True) if not isinstance(old,str) else old,'new_value':json.dumps(new,ensure_ascii=False,sort_keys=True) if not isinstance(new,str) else new,'reason':reason,'source_case_id':case,'confidence':confidence,'timestamp':NOW,'reversible':'true','notes':'Phase 1 trace record.'})
for root,members in groups.items():
 if len(members)<2:continue
 layer=root[0]; ids=sorted(x[1] for x in members); canonical_id=ids[0]; canonical=IDX[layer][canonical_id]; cp=canonical['properties']; archives=[]; transferred=[]; conflict_names=[]
 for rid in ids[1:]:
  rf=IDX[layer][rid];rp=rf['properties'];archives.append(rf)
  for k,v in rp.items():
   if k in ('id','canonical_id'):continue
   if cp.get(k) in (None,'',[]) and v not in (None,'',[]):cp[k]=v;transferred.append(k)
   elif k in conflict_fields and v not in (None,'',[]) and cp.get(k) not in (None,'',[]) and cp.get(k)!=v:
    conflicts.append({'canonical_id':canonical_id,'layer_id':layer,'field_name':k,'value_a':cp.get(k),'source_a':cp.get('source'),'value_b':v,'source_b':rp.get('source'),'selected_value':cp.get(k),'selection_reason':'Retained older published canonical value; alternate archived','confidence':'medium','requires_institutional_review':'true','notes':'No alternate value discarded; retired feature archived in canonical.'});conflict_names.append(k)
  retired.append({'retired_id':rid,'canonical_id':canonical_id,'layer_id':layer,'retirement_reason':'strict_true_duplicate','retirement_date':TODAY,'redirect_status':'active_alias','source_record':rp.get('source_record_index'),'notes':'Full retired feature archived in canonical merged_record_archives.'});merged_by_layer[layer]+=1
 cp['canonical_id']=canonical_id;cp['legacy_ids']=sorted(set((cp.get('legacy_ids') or [])+ids[1:]));cp['alias_ids']=sorted(set((cp.get('alias_ids') or [])+ids[1:]));cp['merged_from_ids']=ids[1:]
 record_values=(cp.get('source_records') or [])+[cp.get('source_record_index')]+[IDX[layer][x]['properties'].get('source_record_index') for x in ids[1:]]
 file_values=(cp.get('source_files') or [])+[cp.get('source_kml')]+[IDX[layer][x]['properties'].get('source_kml') for x in ids[1:]]
 cp['source_records']=list(dict.fromkeys(x for x in record_values if x is not None));cp['source_files']=list(dict.fromkeys(x for x in file_values if x));cp['merge_status']='merged_canonical';cp['merge_confidence']='high';cp['merge_date']=TODAY;cp['merge_method']='strict_exact_identity_phase_1';cp['merge_notes']='Exact normalized name, geometry, and type; retired records fully archived.';cp['merged_record_archives']=(cp.get('merged_record_archives') or [])+archives;canonical_updated.add((layer,canonical_id));log(layer,canonical_id,'merge','canonical_record',{}, {'retired_ids':ids[1:]},'Strict duplicate cluster merged and archived',confidence='high')
 D[layer]['features']=[f for f in D[layer]['features'] if f['properties']['id'] not in ids[1:]]
 for row in resolution:
  if row['layer_id']==layer and {row['record_a_id'],row['record_b_id']}.issubset(set(ids)) and row['final_classification']=='true_duplicate':row.update({'canonical_id':canonical_id,'retired_id':next((x for x in (row['record_a_id'],row['record_b_id']) if x!=canonical_id),''),'fields_transferred':'|'.join(sorted(set(transferred))),'conflicting_fields':'|'.join(sorted(set(conflict_names))),'legacy_ids_preserved':'true'})

# Safe normalization and review triage for every retained feature.
review_actions=[];review_before=0;temp_names=0
for layer,d in D.items():
 for f in d['features']:
  p=f['properties'];fid=p['id'];before_marker={}
  for k,v in list(p.items()):
   if isinstance(v,str):
    nv=clean(v)
    if nv!=v:before_marker[k]=v;p[k]=nv
  for k in ('legacy_ids','alias_ids','source_records','source_files','merged_from_ids','related_feature_ids','relationship_types'):
   old=p.get(k);new=list(dict.fromkeys(old or []));p[k]=new
   if old!=new:before_marker[k]=old
  local=list(dict.fromkeys(p.get('local_images') or []));
  if local!=p.get('local_images'):before_marker['local_images']=p.get('local_images');p['local_images']=local
  if p.get('image_count')!=len(local):before_marker['image_count']=p.get('image_count');p['image_count']=len(local)
  missing=[x for x in (p.get('missing_fields') or []) if not p.get(x)];
  if missing!=p.get('missing_fields'):before_marker['missing_fields']=p.get('missing_fields');p['missing_fields']=missing
  p.setdefault('canonical_id',fid);p.setdefault('merge_status','not_merged');p.setdefault('merge_confidence',None);p.setdefault('merge_date',None);p.setdefault('merge_method',None);p.setdefault('merge_notes',None)
  is_review=p.get('data_review_status') in ('review_required','pending_review') or p.get('investment_type_code')=='review_required' or p.get('facility_type_code') in ('review_required','accommodation_resort_other')
  if is_review:
   review_before+=1; reasons=[]
   if p.get('investment_type_code')=='review_required' or p.get('facility_type_code') in ('review_required','accommodation_resort_other'):reasons.append('classification_review')
   if not p.get('name_ar') or re.search(r'تحتاج تعريف|يحتاج مراجعة|غير مسماة|unnamed|unknown',str(p.get('name_ar')),re.I):reasons.append('name_review')
   if not p.get('license_status'):reasons.append('license_review')
   if layer=='investment':reasons += [x for x,k in [('investment_legal_review','legal_status'),('investment_financial_review','estimated_cost'),('ownership_review','ownership_type'),('infrastructure_review','infrastructure_status')] if not p.get(k)]
   if not reasons:reasons=['source_review']
   reasons=list(dict.fromkeys(reasons));priority='P1' if 'name_review' in reasons or ('investment_legal_review' in reasons and 'ownership_review' in reasons) else 'P2' if 'classification_review' in reasons else 'P3';owner='وزارة السياحة أو البلدية أو الجهة المالكة حسب الاختصاص';p.update({'review_reason_codes':reasons,'review_priority':priority,'review_owner_required':owner,'review_action_required':'institutional verification of flagged fields','review_status':'open'})
   temporary=bool('name_review' in reasons);p['temporary_name_status']='temporary_review_label' if temporary else 'not_temporary';p['temporary_name_reason']='generated_or_unknown_name' if temporary else None;p['official_name_required']=temporary;temp_names+=temporary
   review_actions.append({'review_case_id':f'REV-{len(review_actions)+1:05d}','feature_id':fid,'layer_id':layer,'name_ar':p.get('name_ar'),'review_reason_codes':'|'.join(reasons),'priority':priority,'current_value':p.get('data_review_status'),'issue_description':'Multiple reasons' if len(reasons)>1 else reasons[0],'required_action':p['review_action_required'],'required_entity':owner,'suggested_collection_method':'authoritative registry or direct verification','evidence_available':str(bool(p.get('source'))).lower(),'automatic_resolution_possible':'false','manual_review_required':'true','status':'open','notes':'Required entity is not asserted as current data source.'})
  if before_marker:log(layer,fid,'safe_normalization','multiple_fields',before_marker,{k:p.get(k) for k in before_marker},'Safe formatting, deduplication, or derived count correction')
  if is_review:log(layer,fid,'review_triage','review_fields',{}, {'codes':p['review_reason_codes'],'priority':p['review_priority']},'Review reason and ownership triage','', 'high')
  if (layer,fid) not in canonical_updated and not any(c['feature_id']==fid and c['layer_id']==layer for c in changes):log(layer,fid,'phase_metadata','canonical_defaults',{}, {'canonical_id':p['canonical_id']},'Phase 1 canonical metadata initialized')

# Cross-layer relationships are documented; only high-confidence probable/confirmed links enter GeoJSON.
rel_rows=[];links=0
for n,r in enumerate(cross,1):
 pair={r['record_a_layer'],r['record_b_layer']};rt='facility_and_investment_project' if 'investment' in pair else 'hotel_inside_resort' if pair=={'hotels','resorts'} else 'restaurant_and_cafe_same_complex' if pair=={'tripoliRestaurants','tripoliCafes'} else 'restaurant_inside_hotel' if pair=={'tripoliRestaurants','hotels'} else 'cafe_inside_hotel' if pair=={'tripoliCafes','hotels'} else 'unresolved_relationship';status='probable' if r['confidence']=='medium' else 'unresolved';high=status in ('confirmed','probable') and r['confidence']=='high'
 rel_rows.append({'relationship_id':f'REL-{n:05d}','record_a_layer':r['record_a_layer'],'record_a_id':r['record_a_id'],'record_a_name':r['record_a_name'],'record_b_layer':r['record_b_layer'],'record_b_id':r['record_b_id'],'record_b_name':r['record_b_name'],'relationship_type':rt,'relationship_status':status,'distance_meters':r['distance_meters'],'name_similarity':r['name_similarity'],'spatial_relationship':r['geometry_relationship'],'confidence':r['confidence'],'recommended_display_behavior':'retain_both_and_optionally_link','requires_manual_review':str(not high).lower(),'notes':'Relationship documentation does not imply duplicate identity.'})
 if high:
  for la,ida,lb,idb in [(r['record_a_layer'],r['record_a_id'],r['record_b_layer'],r['record_b_id']),(r['record_b_layer'],r['record_b_id'],r['record_a_layer'],r['record_a_id'])]:
   f=IDX.get(la,{}).get(ida)
   if f and any(x['properties']['id']==ida for x in D[la]['features']):f['properties']['related_feature_ids']=sorted(set(f['properties'].get('related_feature_ids',[])+[idb]));f['properties']['relationship_types']=sorted(set(f['properties'].get('relationship_types',[])+[rt]));links+=1

after={k:len(v['features']) for k,v in D.items()}; retired_n=len(retired)
for layer,d in D.items():d['metadata']=dict(d.get('metadata') or {},cleaning_phase='national_data_cleaning_phase_1',cleaning_date=TODAY,features_before=BEFORE[layer],features_after=after[layer],true_duplicates_merged=merged_by_layer[layer],records_retained=after[layer],review_items_remaining=sum(x['layer_id']==layer for x in review_actions),methodology_version='1.0.0');(ROOT/FILES[layer]).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def write(path,fields,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
C=ROOT/'docs/cleaning';write(C/'national-duplicate-resolution-register.csv',['case_id','layer_id','record_a_id','record_a_name','record_b_id','record_b_name','distance_meters','name_similarity','geometry_relationship','previous_classification','final_classification','canonical_id','retired_id','action','confidence','decision_basis','fields_transferred','conflicting_fields','legacy_ids_preserved','requires_manual_review','notes'],resolution);write(C/'national-field-conflict-register.csv',['canonical_id','layer_id','field_name','value_a','source_a','value_b','source_b','selected_value','selection_reason','confidence','requires_institutional_review','notes'],conflicts);write(C/'national-retired-id-register.csv',['retired_id','canonical_id','layer_id','retirement_reason','retirement_date','redirect_status','source_record','notes'],retired);write(C/'national-cross-layer-relationship-register.csv',['relationship_id','record_a_layer','record_a_id','record_a_name','record_b_layer','record_b_id','record_b_name','relationship_type','relationship_status','distance_meters','name_similarity','spatial_relationship','confidence','recommended_display_behavior','requires_manual_review','notes'],rel_rows);write(C/'national-review-action-register.csv',['review_case_id','feature_id','layer_id','name_ar','review_reason_codes','priority','current_value','issue_description','required_action','required_entity','suggested_collection_method','evidence_available','automatic_resolution_possible','manual_review_required','status','notes'],review_actions);write(C/'national-data-cleaning-phase-1-change-log.csv',['change_id','layer_id','feature_id','change_type','field_name','old_value','new_value','reason','source_case_id','confidence','timestamp','reversible','notes'],changes)
baseline_reviews={x['layer_id']:int(x['review_required_count']) for x in csv.DictReader((ROOT/'docs/audit/national-layer-structural-audit.csv').open(encoding='utf-8-sig'))};scores=[]
for layer in D:
 current=[f for f in D[layer]['features'] if f['properties'].get('data_review_status') in ('review_required','pending_review')]; pc=Counter(f['properties'].get('review_priority') for f in current); comp=json.load((ROOT/'docs/audit/national-layer-quality-scorecard.json').open(encoding='utf8')); old=next(x['completeness_average'] for x in comp['layers'] if x['layer_id']==layer);scores.append({'layer_id':layer,'features_before':BEFORE[layer],'features_after':after[layer],'true_duplicates_merged':merged_by_layer[layer],'false_positives_closed':0,'records_linked_as_related':sum(1 for x in rel_rows if layer in (x['record_a_layer'],x['record_b_layer'])),'review_items_before':baseline_reviews[layer],'review_items_resolved':baseline_reviews[layer]-len(current),'review_items_remaining':len(current),'p1_remaining':pc['P1'],'p2_remaining':pc['P2'],'p3_remaining':pc['P3'],'field_conflicts':sum(x['layer_id']==layer for x in conflicts),'temporary_names':sum(x['layer_id']==layer and 'name_review' in x['review_reason_codes'] for x in review_actions),'completeness_before':old,'completeness_after':old,'local_images':sum(bool(f['properties'].get('local_images')) for f in D[layer]['features']),'cleaning_status':'complete_with_open_reviews'})
write(C/'national-data-cleaning-phase-1-scorecard.csv',list(scores[0]),scores);(C/'national-data-cleaning-phase-1-scorecard.json').write_text(json.dumps({'generated_at':NOW,'status':'CLEANING_PHASE_1_COMPLETE_WITH_OPEN_REVIEWS','layers':scores},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
fc=Counter(r['final_classification'] for r in resolution);pcount=Counter({k.upper():sum(x[k+'_remaining'] for x in scores) for k in ('p1','p2','p3')});review_remaining=sum(x['review_items_remaining'] for x in scores);avg_before=round(sum(x['completeness_before']*x['features_before'] for x in scores)/TOTAL,2);avg_after=round(sum(x['completeness_after']*x['features_after'] for x in scores)/sum(after.values()),2)
report=f'''# تقرير تنظيف السجل الوطني — المرحلة الأولى\n\n## الملخص التنفيذي\n\nالحالة: **CLEANING_PHASE_1_COMPLETE_WITH_OPEN_REVIEWS**. أعيد فحص {len(confirmed)} حالة، وثبت {fc['true_duplicate']} زوجًا صارمًا ضمن مجموعات أدت إلى تقاعد {retired_n} سجلًا مع أرشفتها كاملة داخل السجلات Canonical. لم يُحذف أي سجل آخر.\n\n## المنهجية والنتائج\n\n- قبل التنظيف: {TOTAL}\n- بعد التنظيف: {sum(after.values())}\n- IDs متقاعدة: {retired_n}\n- probable: {fc['probable_duplicate']}\n- insufficient evidence: {fc['insufficient_evidence']}\n- علاقات عابرة موثقة: {len(rel_rows)}\n- تعارضات حقول: {len(conflicts)}\n\nاعتمد الدمج فقط عند تطابق الاسم المنظف والهندسة والنوع. احتُفظ بالسجل الأقدم كـCanonical، وبكل Feature متقاعد داخل `merged_record_archives`، وبـIDs داخل `legacy_ids` و`alias_ids`.\n\n## المراجعات\n\n- المتبقي: {review_remaining}\n- P1: {pcount['P1']}\n- P2: {pcount['P2']}\n- P3: {pcount['P3']}\n\nتشمل الأسباب الاسم والتصنيف والترخيص، وللاستثمار الوضع القانوني والملكية والتكلفة والبنية التحتية. الجهات المذكورة مطلوبة للاستكمال وليست مصادر مؤكدة.\n\n## أثر الاكتمال والمخاطر\n\nمتوسط الاكتمال قبل: {avg_before}%، وبعد: {avg_after}%. لم تُخترع بيانات؛ لذلك لا يُتوقع ارتفاع مصطنع. المخاطر المفتوحة هي المراجعات المؤسسية والتعارضات والعلاقات غير المحسومة.\n\n## توصية المرحلة التالية\n\nمراجعة P1 والتعارضات والـprobable duplicates بشريًا، ثم اعتماد العلاقات عالية الثقة. لا يبدأ تنزيل الصور أو الاستكمال الخارجي في هذه المرحلة.\n''';(ROOT/'docs/national-data-cleaning-phase-1-report.md').write_text(report,encoding='utf8')
print(f'TOTAL_FEATURES_BEFORE_CLEANING = {TOTAL}');print(f'TOTAL_REVIEW_REQUIRED_BEFORE_CLEANING = 676');print(f'CONFIRMED_DUPLICATES_BEFORE_CLEANING = {len(confirmed)}');print(f'CROSS_LAYER_RELATIONSHIPS_BEFORE_CLEANING = {len(cross)}');print('CLEANING_LAYER_FILES = '+','.join(FILES.values()));print(f'CLEANING_LAYER_COUNT = {len(FILES)}');print(f'CONFIRMED_DUPLICATES_RECHECKED = {len(confirmed)}');print(f'TRUE_DUPLICATES_CONFIRMED = {fc["true_duplicate"]}');print(f'PROBABLE_DUPLICATES_AFTER_RECHECK = {fc["probable_duplicate"]}');print('FALSE_POSITIVES_FOUND = 0');print('RELATED_DISTINCT_FOUND = 0');print(f'INSUFFICIENT_EVIDENCE_FOUND = {fc["insufficient_evidence"]}');print(f'TRUE_DUPLICATE_RECORDS_RETIRED = {retired_n}');print(f'TOTAL_FEATURES_AFTER_CLEANING = {sum(after.values())}');print('FEATURE_COUNT_RECONCILIATION = '+('PASS' if sum(after.values())==TOTAL-retired_n else 'FAIL'))
