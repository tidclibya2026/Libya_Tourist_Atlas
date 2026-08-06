import json, subprocess, sys, threading, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/layers/tourism-investment-projects.geojson').read_text(encoding='utf-8'))
features=data['features']; points=sum(f['geometry']['type']=='Point' for f in features); polygons=sum(f['geometry']['type'] in ('Polygon','MultiPolygon') for f in features); multis=data['metadata']['multigeometry_count']
failed=0
def result(name,ok):
 global failed
 print(f'{name} = {"PASS" if ok else "FAIL"}')
 if not ok: failed+=1

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass

server=ThreadingHTTPServer(('127.0.0.1',8765),lambda *a,**k:Quiet(*a,directory=str(ROOT),**k)); threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]; remote=[]; image404=[]; start=time.time()
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True); page=browser.new_page(viewport={'width':1440,'height':1000})
  page.on('console',lambda m: errors.append(m.text) if m.type=='error' else None)
  page.on('pageerror',lambda e: errors.append(str(e)))
  page.on('dialog',lambda d: (errors.append(d.message),d.accept()))
  page.on('request',lambda r: remote.append(r.url) if ('googleusercontent' in r.url or 'mymaps' in r.url) else None)
  page.on('response',lambda r: image404.append(r.url) if r.status==404 and r.request.resource_type=='image' else None)
  page.goto('http://127.0.0.1:8765/index.html',wait_until='networkidle',timeout=60000)
  cb=page.locator('[data-id="investment"]'); page.evaluate("el => { el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true})); }",cb.element_handle()); page.wait_for_function("state.investment && state.investment.count > 0",timeout=60000)
  loaded=page.evaluate('state.investment.count'); has_cluster=page.evaluate('!!state.investment.pointCluster'); has_shapes=page.evaluate('state.investment.shapeGroup.getLayers().length > 0')
  page.evaluate("el => { el.checked=false; el.dispatchEvent(new Event('change',{bubbles:true})); }",cb.element_handle()); off=page.evaluate('!map.hasLayer(state.investment.group)'); page.evaluate("el => { el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true})); }",cb.element_handle()); on=page.evaluate('map.hasLayer(state.investment.group)')
  popup_clean=all(x not in json.dumps(data,ensure_ascii=False) for x in ('undefined','<![CDATA['))
  result('INVESTMENT_LAYER_LOAD',loaded==len(features)); print(f'INVESTMENT_FEATURE_COUNT = {loaded}'); print(f'INVESTMENT_POINT_COUNT = {points}'); print(f'INVESTMENT_POLYGON_COUNT = {polygons}'); print(f'INVESTMENT_MULTIGEOMETRY_COUNT = {multis}')
  result('INVESTMENT_TOGGLE',off and on); result('INVESTMENT_POINTS_CLUSTERING',has_cluster); result('INVESTMENT_POLYGONS_RENDER',has_shapes)
  result('INVESTMENT_POINT_POPUPS',points>=5); result('INVESTMENT_POLYGON_POPUPS',polygons>=5); result('INVESTMENT_FIT_BOUNDS',page.evaluate("typeof fit === 'function'")); result('NO_RAW_HTML',popup_clean); result('NO_EAGER_REMOTE_IMAGE_LOADING',not remote); result('NO_IMAGE_404',not image404); result('NO_CONSOLE_ERRORS',not errors); result('INVESTMENT_INITIAL_RENDER_PERFORMANCE',time.time()-start<30)
  browser.close()
except Exception as e:
 print(f'PLAYWRIGHT_ERROR = {e}'); print('BROWSER_ERRORS = '+json.dumps(errors,ensure_ascii=False)); failed+=1
finally: server.shutdown()
print(f'FAILED = {failed}'); sys.exit(1 if failed else 0)
