import csv,json,sys,threading,time
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.stdout.reconfigure(encoding='utf8');FILES={'hotels':'hotels.geojson','tripoliRestaurants':'tripoli-restaurants.geojson','tripoliCafes':'tripoli-cafes.geojson','resorts':'tourist-villages-resorts.geojson','investment':'tourism-investment-projects.geojson'};DATA={k:json.loads((ROOT/'data/layers'/v).read_text(encoding='utf8')) for k,v in FILES.items()};ret=list(csv.DictReader((ROOT/'docs/cleaning/national-retired-id-register.csv').open(encoding='utf-8-sig')));rel=list(csv.DictReader((ROOT/'docs/cleaning/national-cross-layer-relationship-register.csv').open(encoding='utf-8-sig')));failed=0
def out(n,v):
 global failed
 print(f'{n} = {"PASS" if v else "FAIL"}');failed+=not v
class Q(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=ThreadingHTTPServer(('127.0.0.1',8765),lambda*a,**k:Q(*a,directory=str(ROOT),**k));threading.Thread(target=s.serve_forever,daemon=True).start();errors=[];remote=[];img404=[];loaded=toggle=popup=clean=canonical=legacy=alias_name=related=True;start=time.time()
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1440,'height':1000});page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:remote.append(r.url) if 'googleusercontent' in r.url or 'mymaps.usercontent' in r.url else None);page.on('response',lambda r:img404.append(r.url) if r.status==404 and r.request.resource_type=='image' else None);page.on('dialog',lambda d:d.accept());page.goto('http://127.0.0.1:8765/index.html',wait_until='networkidle')
  for lid,d in DATA.items():
   el=page.locator(f'[data-id="{lid}"]').element_handle();page.evaluate("e=>{e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}))}",el);page.wait_for_function(f"state.{lid}&&state.{lid}.count==={len(d['features'])}",timeout=60000);page.evaluate("e=>{e.checked=false;e.dispatchEvent(new Event('change',{bubbles:true}))}",el);toggle&=page.evaluate(f'!map.hasLayer(state.{lid}.group)');page.evaluate("e=>{e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}))}",el)
  def search(q):
   page.evaluate('map.closePopup()');page.fill('#searchInput',q);page.evaluate('search()');page.wait_for_function("q=>[...document.querySelectorAll('.leaflet-popup')].some(x=>x.innerText.includes(q)||x.innerText.includes('المعرف الوطني'))",arg=q,timeout=8000);return page.locator('.leaflet-popup').last.inner_text()
  m=ret[0];txt=search(m['canonical_id']);canonical&=m['canonical_id'] in txt;txt=search(m['retired_id']);legacy&=m['canonical_id'] in txt and m['retired_id'] not in [f['properties']['id'] for f in DATA[m['layer_id']]['features']];popup&='المعرف الوطني' in txt;clean&=all(x not in txt for x in ('null','undefined','NaN','<![CDATA['))
  alt=next((f['properties']['name_en'] for d in DATA.values() for f in d['features'] if f['properties'].get('name_en')),None);alias_name&=bool(alt and search(alt))
  rr=rel[0];related&=rr['record_a_id'] in {f['properties']['id'] for d in DATA.values() for f in d['features']} or any(rr['record_a_id'] in f['properties'].get('alias_ids',[]) for d in DATA.values() for f in d['features']);b.close()
except Exception as e:errors.append(str(e));loaded=False
finally:s.shutdown()
out('ATLAS_LOAD_AFTER_CLEANING',loaded);out('ALL_CLEANED_LAYERS_RUNTIME',toggle);out('CANONICAL_ID_SEARCH',canonical);out('LEGACY_ID_RESOLUTION',legacy);out('ALIAS_NAME_SEARCH',alias_name);out('MERGED_RECORD_POPUPS',popup);out('RELATED_RECORD_POPUPS',related);out('NO_RETIRED_DUPLICATE_FEATURES',legacy);out('NO_NULL_OR_UNDEFINED',clean);out('NO_RAW_HTML',clean);out('NO_EAGER_REMOTE_IMAGE_LOADING',not remote);out('NO_IMAGE_404',not img404);out('NO_CONSOLE_ERRORS',not errors);out('CLEANING_RUNTIME_PERFORMANCE',time.time()-start<120);print('ERRORS = '+json.dumps(errors,ensure_ascii=False));print(f'FAILED = {failed}');sys.exit(1 if failed else 0)
