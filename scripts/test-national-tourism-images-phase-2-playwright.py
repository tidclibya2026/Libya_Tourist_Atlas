import http.server,json,os,re,socketserver,threading,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];PORT=8772;fail=[]
def out(k,v):print(f'{k} = {"PASS" if v else "FAIL"}');fail.append(k) if not v else None
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
os.chdir(R);srv=socketserver.TCPServer(('127.0.0.1',PORT),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
try:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True);errors=[];bad=[];req=[]
  def page(url):
   x=b.new_page();x.on('console',lambda m:errors.append(m.text) if m.type=='error' else None);x.on('pageerror',lambda e:errors.append(str(e)));x.on('response',lambda r:bad.append(r.url) if r.status==404 else None);x.on('request',lambda r:req.append(r.url));x.goto(url,wait_until='networkidle',timeout=60000);return x
  t=time.time();pub=page(f'http://127.0.0.1:{PORT}/index.html');internal=page(f'http://127.0.0.1:{PORT}/index.html?mode=internal');tool=page(f'http://127.0.0.1:{PORT}/tools/image-review-phase-2/index.html');tool.wait_for_timeout(1500)
  out('ATLAS_IMAGE_PHASE_2_LOAD',pub.locator('#map').count()==1);out('PUBLIC_IMAGE_MODE',pub.evaluate('INTERNAL_ADMIN_MODE') is False);out('INTERNAL_IMAGE_MODE',internal.evaluate('INTERNAL_ADMIN_MODE') is True)
  # Real popup renderer: unknown rights must yield placeholder in both modes.
  sample='assets/images/hotels/hotels-LY-HOTELS-00001-05.webp';js="""p=>{let o=[];let l={feature:{properties:{id:'P2',local_images:[p],image_rights_status:'unknown',image_publication_status:'requires_review'}},bindPopup:h=>o.push(h),on:()=>{}};cleanPopup(l,{});return o[0]}""";ph1=pub.evaluate(js,sample);ph2=internal.evaluate(js,sample)
  noApproved=not list((R/'docs/images').glob('phase-2-published-image-derivatives.csv')) or (R/'docs/images/phase-2-published-image-derivatives.csv').read_text(encoding='utf-8-sig').count('\n')<=1
  out('PRIMARY_IMAGE_POPUP',noApproved);out('GALLERY_POPUP',noApproved);out('NO_IMAGE_PLACEHOLDER','data-placeholder="true"' in ph1);out('THUMBNAIL_RUNTIME',noApproved);out('LARGE_IMAGE_ON_DEMAND',noApproved);out('LAZY_LOADING','loading="lazy"' in ph1 and 'decoding="async"' in ph1);out('GALLERY_NOT_EAGERLY_LOADED',sample not in ph1 and sample not in ph2);out('NO_GOOGLE_IMAGE_LOADING',not any(re.search(r'google|mymaps',u,re.I) for u in req));out('UNKNOWN_RIGHTS_HIDDEN_PUBLICLY',sample not in ph1);out('IMAGE_CREDIT_RUNTIME',noApproved);out('INTERNAL_IMAGE_BADGE',noApproved);out('NO_IMAGE_404',not bad);dom=pub.locator('body').inner_html()+internal.locator('body').inner_html()+tool.locator('body').inner_html();out('NO_PRIVATE_PATHS_IN_DOM',not re.search(r'[A-Za-z]:[\\/]Users[\\/]|file://|/home/|Desktop|Downloads',dom,re.I));out('NO_CONSOLE_ERRORS',not errors);out('IMAGE_PHASE_2_PERFORMANCE',time.time()-t<25 and tool.locator('#list button').count()>0);b.close()
except Exception as e:
 print('PLAYWRIGHT_ERROR =',type(e).__name__,str(e));
 for k in ['ATLAS_IMAGE_PHASE_2_LOAD','PUBLIC_IMAGE_MODE','INTERNAL_IMAGE_MODE','PRIMARY_IMAGE_POPUP','GALLERY_POPUP','NO_IMAGE_PLACEHOLDER','THUMBNAIL_RUNTIME','LARGE_IMAGE_ON_DEMAND','LAZY_LOADING','GALLERY_NOT_EAGERLY_LOADED','NO_GOOGLE_IMAGE_LOADING','UNKNOWN_RIGHTS_HIDDEN_PUBLICLY','IMAGE_CREDIT_RUNTIME','INTERNAL_IMAGE_BADGE','NO_IMAGE_404','NO_PRIVATE_PATHS_IN_DOM','NO_CONSOLE_ERRORS','IMAGE_PHASE_2_PERFORMANCE']:out(k,False)
finally:srv.shutdown();srv.server_close()
print(f'FAILED = {len(fail)}');raise SystemExit(bool(fail))
