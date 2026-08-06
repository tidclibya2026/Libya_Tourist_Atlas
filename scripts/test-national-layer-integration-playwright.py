import json,sys,threading,time
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
LAYERS={'hotels':'data/layers/hotels.geojson','tripoliRestaurants':'data/layers/tripoli-restaurants.geojson','tripoliCafes':'data/layers/tripoli-cafes.geojson','resorts':'data/layers/tourist-villages-resorts.geojson','investment':'data/layers/tourism-investment-projects.geojson'}
DATA={k:json.loads((ROOT/v).read_text(encoding='utf8')) for k,v in LAYERS.items()}; failed=0
def out(n,v):
 global failed
 print(f'{n} = {"PASS" if v else "FAIL"}'); failed+=not v
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',8765),lambda *a,**k:Quiet(*a,directory=str(ROOT),**k));threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[];remote=[];image404=[];dialogs=[];popup_issues=[];runtime={};popup_ok=True;start=time.time();page_loaded=False;toggle_ok=True;cluster_ok=True;polygon_ok=True;fit_ok=True;search_ok=True
def re_remote(url):return 'googleusercontent' in url or 'mymaps.usercontent' in url
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1000})
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:remote.append(r.url) if re_remote(r.url) else None);page.on('response',lambda r:image404.append(r.url) if r.status==404 and r.request.resource_type=='image' else None);page.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
  page.goto('http://127.0.0.1:8765/index.html',wait_until='networkidle',timeout=60000);page_loaded=page.title()!=''
  for lid,d in DATA.items():
   t=time.time();el=page.locator(f'[data-id="{lid}"]').element_handle();page.evaluate("el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}",el);page.wait_for_function(f"state.{lid} && state.{lid}.count === {len(d['features'])}",timeout=60000);runtime[lid]=time.time()-t
   cluster_ok &= page.evaluate(f"!!state.{lid}.pointCluster && state.{lid}.pointCluster.getLayers().length>0")
   if lid=='investment':polygon_ok &= page.evaluate("state.investment.shapeGroup.getLayers().length>0")
   first=next(f for f in d['features'] if (f.get('properties') or {}).get('name_ar'));q=first['properties']['name_ar'];page.evaluate('map.closePopup()');page.fill('#searchInput',q);page.evaluate('search()');page.wait_for_function("q=>[...document.querySelectorAll('.leaflet-popup')].some(x=>x.innerText.includes(q))",arg=q,timeout=5000);match=page.locator('.leaflet-popup').filter(has_text=q).last;search_ok &= match.count()>0
   if match.count():
    txt=match.inner_text();clean=q in txt and all(x not in txt for x in ('null','undefined','<![CDATA[','NaN'));popup_ok &= clean
    if not clean:popup_issues.append({'layer':lid,'query':q,'popup':txt[:500]})
   fit_ok &= page.evaluate('map.getBounds().isValid()');page.evaluate("el=>{el.checked=false;el.dispatchEvent(new Event('change',{bubbles:true}))}",el);toggle_ok &= page.evaluate(f"!map.hasLayer(state.{lid}.group)")
  # All layers sequentially enabled after independent checks.
  for lid in LAYERS: page.evaluate(f"toggleLayer(layers.find(x=>x.id==='{lid}'),true)")
  page.wait_for_timeout(500);all_on=all(page.evaluate(f"map.hasLayer(state.{lid}.group)") for lid in LAYERS)
  memory=page.evaluate("performance.memory ? performance.memory.usedJSHeapSize : 0");browser.close()
except Exception as e:errors.append(f'PLAYWRIGHT_ERROR: {e}')
finally:server.shutdown()
out('ATLAS_PAGE_LOAD',page_loaded);out('HOTELS_LAYER_RUNTIME',runtime.get('hotels',99)<20);out('RESTAURANTS_LAYER_RUNTIME',runtime.get('tripoliRestaurants',99)<20);out('CAFES_LAYER_RUNTIME',runtime.get('tripoliCafes',99)<20);out('RESORTS_LAYER_RUNTIME',runtime.get('resorts',99)<20);out('INVESTMENT_LAYER_RUNTIME',runtime.get('investment',99)<25);out('ALL_LAYERS_SEQUENTIAL_TOGGLE',toggle_ok and locals().get('all_on',False));out('POINT_CLUSTERING_RUNTIME',cluster_ok);out('POLYGON_RENDER_RUNTIME',polygon_ok);out('POPUPS_RUNTIME',popup_ok and search_ok);out('FIT_BOUNDS_RUNTIME',fit_ok);out('NO_NULL_OR_UNDEFINED',popup_ok);out('NO_RAW_HTML',popup_ok);out('NO_EAGER_REMOTE_IMAGE_LOADING',not remote);out('NO_IMAGE_404',not image404);out('NO_CONSOLE_ERRORS',not errors);out('ATLAS_RUNTIME_PERFORMANCE',time.time()-start<60 and locals().get('memory',0)<500_000_000);print('POPUP_ISSUES = '+json.dumps(popup_issues,ensure_ascii=False));print('RUNTIME_ERRORS = '+json.dumps(errors,ensure_ascii=False));print(f'FAILED = {failed}');sys.exit(1 if failed else 0)
