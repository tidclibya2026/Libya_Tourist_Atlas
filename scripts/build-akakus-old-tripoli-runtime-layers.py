from lxml import etree
from pathlib import Path
import json,re,csv,html
R=Path(__file__).resolve().parents[1];B=R/'docs/images/batch-1';OUT=R/'data/layers'; parser=etree.XMLParser(recover=True,huge_tree=True)
def text(n,xpath):
 a=n.xpath(xpath); return (str(a[0]) if isinstance(a[0],str) else ''.join(a[0].itertext())).strip() if a else ''
def parse(file,layer,prefix):
 root=etree.parse(str(file),parser);out=[]
 for i,p in enumerate(root.xpath('//*[local-name()="Placemark"]')):
  name=text(p,'./*[local-name()="name"]//text()'); ext={}
  for d in p.xpath('.//*[local-name()="Data"]'):
   k=d.get('name','');v=text(d,'.//*[local-name()="value"]//text()');
   if k:ext[k]=v
  fid=ext.get('atlas_id') or ext.get('feature_id') or f'{prefix}-{i+1:04d}'
  if layer=='akakus': fid=fid.replace('LY-AKAKUS-','LY-AKA-')
  coords=[]
  for c in p.xpath('.//*[local-name()="coordinates"]//text()'):
   for part in c.strip().split():
    q=part.split(',');
    if len(q)>=2:
     try:coords.append([float(q[0]),float(q[1])])
     except:pass
  geom={'type':'Point','coordinates':coords[0] if coords else [0,0]}
  out.append({'type':'Feature','id':fid,'properties':{'id':fid,'name_ar':name,'name_en':name,'layer_id':layer,'category':'أكاكوس' if layer=='akakus' else 'المدينة القديمة طرابلس','source':'KML conversion','source_file':str(file.relative_to(R)).replace('\\','/'),'source_record':i,'data_status':'provisional','publication_status':'published','geometry_status':'valid' if coords else 'invalid','image_review_status':'institutionally_approved_pending_visual_verification','image_publication_status':'provisional_publication_candidate','image_link_status':'runtime_linked_pending_visual_verification','image_rights_status':'institutional_publication_approval','image_governance_version':'runtime_linkage_phase_v1'},'geometry':geom})
 return {'type':'FeatureCollection','features':out,'metadata':{'source_file':str(file.relative_to(R)).replace('\\','/'),'generated_by':'build-akakus-old-tripoli-runtime-layers.py','methodology_version':'runtime_linkage_phase_v1'}}
for file,layer,prefix in [(R/'data/kml/final/akakus.kml','akakus','LY-AKAKUS-COMP'),(R/'data/kml/final/old-tripoli.kml','old-tripoli','LY-TRIPOLI-OLD-CITY-LM')]:
 g=parse(file,layer,prefix); (OUT/f'{layer}.geojson').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf8'); print(layer,len(g['features']))
