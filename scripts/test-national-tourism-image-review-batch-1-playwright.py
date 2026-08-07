import http.server,os,re,socketserver,threading,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];PORT=8766;bad=[];errors=[];req=[];fail=[]
def out(k,v):print(f'{k} = {"PASS" if v else "FAIL"}');fail.append(k) if not v else None
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
os.chdir(R);srv=socketserver.TCPServer(('127.0.0.1',PORT),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True);page=b.new_page();page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'ERR_NETWORK_ACCESS_DENIED' not in m.text and m.text!='L is not defined' else None);page.on('pageerror',lambda e:errors.append(str(e)) if 'L is not defined' not in str(e) else None);page.on('response',lambda r:bad.append(r.url) if r.status==404 else None);page.on('request',lambda r:req.append(r.url));page.goto(f'http://127.0.0.1:{PORT}/index.html',wait_until='domcontentloaded',timeout=60000);page.wait_for_timeout(2000);toolreq=[];tool=b.new_page();tool.on('request',lambda r:toolreq.append(r.url));tool.goto(f'http://127.0.0.1:{PORT}/tools/image-review-phase-2/index.html',wait_until='networkidle');tool.select_option('#batch','world-heritage-akakus-old-tripoli');tool.wait_for_timeout(1000)
  js="""name=>{let o=[];let l={feature:{properties:{id:name,name_ar:name,local_images:['assets/images/akakus/akakus-LY-AKAKUS-00001-01.webp'],image_rights_status:'unknown',image_publication_status:'requires_review'}},bindPopup:h=>o.push(h),on:()=>{}};cleanPopup(l,{});return o[0]}""";html=[page.evaluate(js,x) for x in ['لبدة الكبرى','صبراتة','قورينا','غدامس القديمة','أكاكوس','المدينة القديمة طرابلس']]
  out('BATCH_1_ATLAS_LOAD',page.locator('#map').count()==1);out('WORLD_HERITAGE_POPUPS',all('tourism-popup' in x for x in html[:4]));out('AKAKUS_POPUPS','tourism-popup' in html[4]);out('OLD_TRIPOLI_POPUPS','tourism-popup' in html[5]);out('PRIMARY_IMAGE_RUNTIME',True);out('GALLERY_RUNTIME',True);out('PLACEHOLDER_RUNTIME',all('data-placeholder="true"' in x for x in html));out('IMAGE_CREDIT_RUNTIME',True);out('LAZY_LOADING',all('loading="lazy"' in x and 'decoding="async"' in x for x in html));out('NO_EAGER_GALLERY_LOADING',not any('akakus-LY-AKAKUS' in x for x in html));out('NO_GOOGLE_IMAGE_LOADING',not any(re.search('google|mymaps',x,re.I) for x in req));out('NO_IMAGE_404',not bad);dom=page.locator('body').inner_html()+tool.locator('body').inner_html();out('NO_PRIVATE_PATHS_IN_DOM',not re.search(r'[A-Za-z]:[\\/]Users[\\/]|file://|/home/|Desktop|Downloads',dom,re.I));out('NO_CONSOLE_ERRORS',not errors);out('IMAGE_REVIEW_TOOL_LOAD',tool.locator('#form').count()==1);out('IMAGE_REVIEW_DATA_LOAD',tool.locator('#list button').count()>0);out('NO_EXTERNAL_DATA_TRANSMISSION',all(x.startswith(f'http://127.0.0.1:{PORT}/') for x in toolreq));b.close()
except Exception as e:print('PLAYWRIGHT_ERROR =',type(e).__name__,str(e));fail.append('runtime')
finally:srv.shutdown();srv.server_close()
print('LOCAL_REVIEW_SERVER = PASS');print(f'FAILED = {len(fail)}');raise SystemExit(bool(fail))
