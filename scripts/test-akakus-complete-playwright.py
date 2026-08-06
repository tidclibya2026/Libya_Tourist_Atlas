import sys,json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];failed=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:failed.append(r.url));page.goto('http://localhost:8000/?akakus-complete-test=1',wait_until='domcontentloaded',timeout=60000);page.wait_for_function("typeof window.__atlasTest==='object'");page.wait_for_timeout(700)
 count=page.evaluate("""()=>{let n=0;function w(x){if(!x?.getLayers)return;for(const y of x.getLayers()){const q=y.feature?.properties||{};if(q.id==='WH-WORLD-C0003'||q.parent_site_id==='WH-LY-004')n++;w(y)}};for(const s of Object.values(window.__atlasTest.state))w(s.group);return n}""")
 expected=page.evaluate("""async()=>{const d=await (await fetch('data/layers/world-heritage.geojson')).json();return d.features.filter(f=>f.id==='WH-WORLD-C0003'||f.properties?.parent_site_id==='WH-LY-004').length}""")
 print('AKAKUS_FEATURES_RENDERED =','PASS' if count==expected else 'FAIL',count,expected)
 ok=page.evaluate("""()=>{let f;function w(x){if(f||!x?.getLayers)return;for(const y of x.getLayers()){if(y.feature?.properties?.id==='WH-WORLD-C0003'){f=y;return}w(y)}};for(const s of Object.values(window.__atlasTest.state))w(s.group);if(!f)return false;for(const s of Object.values(window.__atlasTest.state))s.group?.removeLayer?.(f);f.addTo(window.__atlasTest.map);f.fire('click');return true}""");page.wait_for_timeout(500);title=page.locator('.popup-title').inner_text() if page.locator('.popup-title').count() else '';print('AKAKUS_MAIN_POPUP =','PASS' if ok and title else 'FAIL',title)
 print('AKAKUS_NO_404 =','PASS' if not failed else 'FAIL');print('AKAKUS_NO_CONSOLE_ERRORS =','PASS' if not errors else 'FAIL');print('AKAKUS_FAILED =',len(failed)+len(errors));b.close()
