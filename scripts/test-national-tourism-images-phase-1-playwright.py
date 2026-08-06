import contextlib,http.server,json,os,re,socketserver,subprocess,threading,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]; PORT=8768; failures=[]
def result(k,ok): print(f'{k} = {"PASS" if ok else "FAIL"}'); failures.append(k) if not ok else None
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a): pass
os.chdir(R); server=socketserver.TCPServer(('127.0.0.1',PORT),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True);page=b.new_page();errors=[];bad=[];requests=[]
  page.on('console',lambda m: errors.append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda r:bad.append(r.url) if r.status==404 else None);page.on('request',lambda r:requests.append(r.url))
  t=time.time();page.goto(f'http://127.0.0.1:{PORT}/index.html',wait_until='networkidle',timeout=60000);load=time.time()-t
  result('ATLAS_IMAGE_RUNTIME',page.locator('#map').count()==1)
  # Toggle actual registered GeoJSON layers and open available marker popups.
  for lid in ['hotels','tripoliRestaurants','tripoliCafes','resorts','investment','heritage']:
   cb=page.locator(f'input[data-layer-id="{lid}"]');
   if cb.count() and not cb.is_checked(): cb.check();page.wait_for_timeout(500)
  markers=page.locator('.leaflet-marker-icon');
  if markers.count(): markers.first.click(force=True);page.wait_for_timeout(500)
  # Exercise the real popup renderer for both a confirmed local image and the
  # no-image placeholder, independent of marker clustering/viewport state.
  sample=''
  for gp in R.glob('data/layers/*.geojson'):
   try:
    for f in json.loads(gp.read_text(encoding='utf8')).get('features',[]):
     for x in f.get('properties',{}).get('local_images') or []:
      if isinstance(x,str) and not x.startswith(('http://','https://')) and (R/x).exists(): sample=x;break
     if sample:break
   except Exception:pass
   if sample:break
  rendered=page.evaluate("""sample=>{let out=[];for(const props of [{id:'TEST-NO-IMAGE'},{id:'TEST-LOCAL-IMAGE',local_images:[sample]}]){const layer={feature:{properties:props},bindPopup:h=>out.push(h),on:()=>{}};cleanPopup(layer,{})}return out}""",sample)
  page.evaluate("html=>{const x=document.createElement('div');x.id='image-governance-popup-tests';x.innerHTML=html.join('');document.body.appendChild(x)}",rendered)
  imgs=page.locator('#image-governance-popup-tests img');dom=page.locator('body').inner_html();visible=page.locator('#image-governance-popup-tests').inner_text()
  result('LOCAL_IMAGE_POPUPS',bool(sample) and any(sample in x for x in rendered));result('NO_IMAGE_PLACEHOLDER',any('data-placeholder="true"' in x for x in rendered));result('THUMBNAIL_LOADING',imgs.count()>0 and all((imgs.nth(i).get_attribute('src') or '') for i in range(imgs.count())));gallery_ok='<![CDATA[' not in visible and all(x.strip().casefold() not in ('null','undefined','nan') for x in visible.splitlines());result('GALLERY_RUNTIME',gallery_ok);result('LAZY_LOADING',imgs.count()>0 and all(imgs.nth(i).get_attribute('loading')=='lazy' and imgs.nth(i).get_attribute('decoding')=='async' for i in range(imgs.count())));page.wait_for_timeout(500);result('NO_IMAGE_404',not bad);result('NO_EAGER_REMOTE_IMAGE_LOADING',not any(('googleusercontent' in u or 'google.com/maps' in u or 'mymaps' in u) for u in requests));result('NO_PRIVATE_PATHS_IN_DOM',not re.search(r'[A-Za-z]:[\\/]Users[\\/]|file://|/home/|Desktop|Downloads',dom,re.I));result('NO_CONSOLE_ERRORS',not errors);result('IMAGE_RUNTIME_PERFORMANCE',load<15);b.close()
except Exception as e:
 print('PLAYWRIGHT_ERROR =',type(e).__name__,str(e));
 for k in ['ATLAS_IMAGE_RUNTIME','LOCAL_IMAGE_POPUPS','NO_IMAGE_PLACEHOLDER','THUMBNAIL_LOADING','GALLERY_RUNTIME','LAZY_LOADING','NO_IMAGE_404','NO_EAGER_REMOTE_IMAGE_LOADING','NO_PRIVATE_PATHS_IN_DOM','NO_CONSOLE_ERRORS','IMAGE_RUNTIME_PERFORMANCE']: result(k,False)
finally: server.shutdown();server.server_close()
print(f'FAILED = {len(failures)}');raise SystemExit(1 if failures else 0)
