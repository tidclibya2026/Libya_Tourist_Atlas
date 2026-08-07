import http.server, socketserver, threading, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; checks=[]; console_errors=[]; page_errors=[]; external=[]; failed=[]; not_found=[]
def check(k,v): print(f"{k} = {'PASS' if v else 'FAIL'}"); checks.append(bool(v))
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
os.chdir(ROOT); srv=socketserver.TCPServer(("127.0.0.1",0),H); port=srv.server_address[1]; threading.Thread(target=srv.serve_forever,daemon=True).start(); origin=f"http://127.0.0.1:{port}"
try:
  with sync_playwright() as p:
    b=p.chromium.launch(headless=True); page=b.new_page(); page.add_init_script("window.__ATLAS_OFFLINE__=true")
    page.on("console",lambda m: console_errors.append(m.text) if m.type=="error" else None); page.on("pageerror",lambda e: page_errors.append(str(e))); page.on("request",lambda r: external.append(r.url) if not r.url.startswith(origin) else None); page.on("requestfailed",lambda r: failed.append(r.url)); page.on("response",lambda r: not_found.append(r.url) if r.status==404 else None)
    page.goto(origin+"/index.html",wait_until="domcontentloaded",timeout=60000); page.wait_for_function("typeof window.__atlasTest==='object'"); page.wait_for_timeout(300)
    check("ATLAS_LOAD",page.locator("#map").count()==1); check("LEAFLET_RUNTIME",page.evaluate("typeof window.L==='object'"))
    def layer_test(id):
      cb=page.locator(f'input[data-id="{id}"]'); cb.evaluate("el=>el.click()"); page.wait_for_function(f"Object.keys(window.__atlasTest.state).includes('{id}') && !!window.__atlasTest.state['{id}'].group"); page.wait_for_timeout(400)
      return page.evaluate(f"()=>window.__atlasTest.state['{id}'].count || window.__atlasTest.state['{id}'].group.getLayers().length")
    a=layer_test("akakus"); o=layer_test("oldTripoli"); check("AKAKUS_LAYER_LOAD",a>0); check("OLD_TRIPOLI_LAYER_LOAD",o>0)
    check("AKAKUS_SEARCH", page.evaluate("document.body.innerText.includes('تادرارت أكاكوس')")); check("OLD_TRIPOLI_SEARCH",page.evaluate("document.body.innerText.includes('المدينة القديمة طرابلس')"))
    check("AKAKUS_POPUP",page.evaluate("!!window.__atlasTest.state.akakus.group")); check("OLD_TRIPOLI_POPUP",page.evaluate("!!window.__atlasTest.state.oldTripoli.group"))
    check("PROVISIONAL_IMAGE_BADGE",page.evaluate("async()=>{for(const p of [\x27data/layers/akakus.geojson\x27,\x27data/layers/old-tripoli.geojson\x27]){const d=await (await fetch(p)).json();if(d.features.some(f=>f.properties?.image_display_status===\x27provisional\x27))return true;}return false;}"))
    check("NO_FALSE_VERIFIED_LABEL",not page.locator("body").inner_text().lower().__contains__("verified"))
    check("NO_KML_RUNTIME_REQUESTS",not any(".kml" in u.lower() for u in external+failed)); check("NO_EXTERNAL_RUNTIME_REQUESTS",not external); check("NO_IMAGE_404",not not_found); check("NO_CONSOLE_ERRORS",not console_errors); check("NO_PAGE_ERRORS",not page_errors)
    print("CONSOLE_ERRORS =",console_errors); print("PAGE_ERRORS =",page_errors); print("EXTERNAL_REQUESTS =",external); print("FAILED_REQUESTS =",failed); print("IMAGE_404S =",not_found); b.close()
finally: srv.shutdown(); srv.server_close()
print("FAILED =",sum(1 for x in checks if not x)+(1 if console_errors or page_errors or external or failed or not_found else 0))
