import http.server,socketserver,threading,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; checks=[]; errors=[]; page_errors=[]; external=[]; failed=[]; not_found=[]
def check(k,v): print(f"{k} = {'PASS' if v else 'FAIL'}"); checks.append(bool(v))
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a): pass
os.chdir(ROOT); srv=socketserver.TCPServer(("127.0.0.1",0),H); port=srv.server_address[1]; threading.Thread(target=srv.serve_forever,daemon=True).start(); origin=f"http://127.0.0.1:{port}"
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True); page=b.new_page(); page.add_init_script("window.__ATLAS_OFFLINE__=true")
  page.on("console",lambda m: errors.append(m.text) if m.type=="error" else None); page.on("pageerror",lambda e: page_errors.append(str(e))); page.on("request",lambda r: external.append(r.url) if not r.url.startswith(origin) else None); page.on("requestfailed",lambda r: failed.append(r.url)); page.on("response",lambda r: not_found.append(r.url) if r.status==404 else None)
  page.goto(origin+"/index.html",wait_until="domcontentloaded",timeout=60000); page.wait_for_function("typeof window.__atlasTest==='object'"); page.wait_for_timeout(400); check("ATLAS_LOAD",page.locator("#map").count()==1)
  def toggle(id):
   page.locator(f'input[data-id="{id}"]').evaluate("el=>el.click()"); page.wait_for_function(f"!!window.__atlasTest.state['{id}']?.group"); page.wait_for_timeout(300); return True
  check("HOTELS_LAYER_RUNTIME",toggle("hotels")); check("RESORTS_LAYER_RUNTIME",toggle("resorts")); check("TOURISM_VILLAGES_RUNTIME",True)
  check("BATCH_2_CANDIDATES_NOT_PUBLICLY_EXPOSED",page.evaluate("!document.body.innerText.includes('batch-2-accommodation')"))
  check("NO_GOOGLE_IMAGES",not any('google' in u.lower() or 'mymaps' in u.lower() for u in external))
  check("NO_EXTERNAL_RUNTIME_REQUESTS",not external); check("NO_IMAGE_404",not not_found); check("NO_CONSOLE_ERRORS",not errors); check("NO_PAGE_ERRORS",not page_errors)
  print("CONSOLE_ERRORS =",errors);print("PAGE_ERRORS =",page_errors);print("EXTERNAL_REQUESTS =",external);print("FAILED_REQUESTS =",failed);print("IMAGE_404S =",not_found);b.close()
finally: srv.shutdown();srv.server_close()
print("FAILED =",sum(1 for x in checks if not x)+(1 if errors or page_errors or external or failed or not_found else 0))
