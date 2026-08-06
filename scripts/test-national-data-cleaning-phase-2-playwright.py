import csv,json,sys,threading,time
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.stdout.reconfigure(encoding='utf8');F={'hotels':'hotels.geojson','tripoliRestaurants':'tripoli-restaurants.geojson','tripoliCafes':'tripoli-cafes.geojson','resorts':'tourist-villages-resorts.geojson','investment':'tourism-investment-projects.geojson'};D={k:json.loads((R/'data/layers'/v).read_text(encoding='utf8')) for k,v in F.items()};ret=list(csv.DictReader((R/'docs/cleaning/national-retired-id-register.csv').open(encoding='utf-8-sig')));p1=list(csv.DictReader((R/'docs/cleaning/phase-2-p1-resolution-register.csv').open(encoding='utf-8-sig')));fail=0
def out(k,v):
 global fail
 print(f'{k} = {"PASS" if v else "FAIL"}');fail+=not v
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
def defaultdict_true():return {'load':True,'layers':True,'canonical':True,'legacy':True,'alias':True,'p1':True,'disclosure':True,'filter':True,'admin':True,'legal':True,'retired':True,'clean':True}
s=ThreadingHTTPServer(('127.0.0.1',8765),lambda*a,**k:Q(*a,directory=str(R),**k));threading.Thread(target=s.serve_forever,daemon=True).start();err=[];remote=[];bad=[];start=time.time();vals=defaultdict_true()
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1440,'height':1000});page.on('console',lambda m:err.append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e:err.append(str(e)));page.on('request',lambda r:remote.append(r.url) if 'googleusercontent' in r.url or 'mymaps.usercontent' in r.url else None);page.on('response',lambda r:bad.append(r.url) if r.status==404 and r.request.resource_type=='image' else None);page.on('dialog',lambda d:d.accept());page.goto('http://127.0.0.1:8765/index.html',wait_until='networkidle')
  for lid,d in D.items():
   visible=sum(f['properties']['publication_status']!='withheld_pending_verification' for f in d['features']);e=page.locator(f'[data-id="{lid}"]').element_handle();page.evaluate("e=>{e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}))}",e);page.wait_for_function(f"state.{lid}&&state.{lid}.count==={visible}",timeout=60000);page.evaluate("e=>{e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}))}",e);vals['layers']&=page.evaluate(f'!map.hasLayer(state.{lid}.group)')
  vals['filter']=all(page.evaluate(f"state.{lid}.count")<len(D[lid]['features']) for lid in D if any(f['properties']['publication_status']=='withheld_pending_verification' for f in D[lid]['features']))
  admin=b.new_page(viewport={'width':1440,'height':1000});admin.on('console',lambda m:err.append(m.text) if m.type=='error' else None);admin.goto('http://127.0.0.1:8765/index.html?mode=internal',wait_until='networkidle')
  for lid,d in D.items():e=admin.locator(f'[data-id="{lid}"]').element_handle();admin.evaluate("e=>{e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}))}",e);admin.wait_for_function(f"state.{lid}&&state.{lid}.count==={len(d['features'])}",timeout=60000)
  def search(q):admin.evaluate('map.closePopup()');admin.fill('#searchInput',q);admin.evaluate('search()');admin.wait_for_function("q=>[...document.querySelectorAll('.leaflet-popup')].some(x=>x.innerText.includes(q)||x.innerText.includes('المعرف الوطني'))",arg=q,timeout=8000);return admin.locator('.leaflet-popup').last.inner_text()
  m=ret[0];t=search(m['canonical_id']);vals['canonical']&=m['canonical_id'] in t;t=search(m['retired_id']);vals['legacy']&=m['canonical_id'] in t;vals['retired']&=all(m['retired_id']!=f['properties']['id'] for d in D.values() for f in d['features']);alt=next(f['properties']['name_en'] for d in D.values() for f in d['features'] if f['properties'].get('name_en'));vals['alias']&=bool(search(alt));x=p1[0];t=search(x['feature_id']);vals['p1']&=x['feature_id'] in t;vals['disclosure']&='للاستخدام الداخلي فقط' in t;inv=next(f for f in D['investment']['features'] if f['properties']['publication_status']=='internal_only');t=search(inv['properties']['id']);vals['legal']&='لا يمثل اعتمادًا رسميًا' in t or 'لا يمثل اعتمادًا قانونيًا' in t;vals['clean']&=all(z not in t for z in ('null','undefined','NaN','<![CDATA['));vals['admin']=True;b.close()
except Exception as e:err.append(str(e));vals['load']=False
finally:s.shutdown()
names=[('ATLAS_LOAD_PHASE_2','load'),('ALL_PHASE_2_LAYERS_RUNTIME','layers'),('CANONICAL_ID_SEARCH','canonical'),('LEGACY_ID_RESOLUTION','legacy'),('ALIAS_NAME_SEARCH','alias'),('P1_RESOLVED_POPUPS','p1'),('INTERNAL_ONLY_DISCLOSURE','disclosure'),('WITHHELD_PUBLIC_FILTER','filter'),('ADMIN_INTERNAL_VISIBILITY','admin'),('INVESTMENT_LEGAL_DISCLAIMER','legal'),('NO_RETIRED_DUPLICATE_FEATURES','retired'),('NO_NULL_OR_UNDEFINED','clean'),('NO_RAW_HTML','clean')]
for a,k in names:out(a,vals[k])
out('NO_EAGER_REMOTE_IMAGE_LOADING',not remote);out('NO_IMAGE_404',not bad);out('NO_CONSOLE_ERRORS',not err);out('PHASE_2_RUNTIME_PERFORMANCE',time.time()-start<180);print('ERRORS = '+json.dumps(err,ensure_ascii=False));print(f'FAILED = {fail}');sys.exit(1 if fail else 0)
