from playwright.sync_api import sync_playwright
import json

KEYS = {
    "main": "WH-WORLD-C0001",
    "theatre": "WH-LY-002-C0042",
    "mausoleum": "WH-LY-002-C0043",
    "museum": "WH-LY-002-C0019",
    "baths": "WH-LY-002-C0014",
    "forum": "WH-LY-002-C0006",
    "mosaic": "WH-LY-002-C0041",
}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True); page=browser.new_page(viewport={"width":1440,"height":1000})
    errors=[]; failed=[]; page.on("pageerror",lambda e:errors.append(str(e))); page.on("requestfailed",lambda r:failed.append(r.url))
    page.goto("http://localhost:8000/?sabratha-complete-test=1",wait_until="domcontentloaded",timeout=60000); page.wait_for_function("typeof window.__atlasTest==='object'"); page.wait_for_timeout(900)
    found=page.evaluate("""keys=>{const out={};function walk(x){if(!x?.getLayers)return;for(const y of x.getLayers()){const id=y.feature?.properties?.id;if(id)out[id]=y;walk(y)}};for(const s of Object.values(window.__atlasTest.state))walk(s.group);return Object.keys(keys).reduce((a,k)=>{a[k]=Boolean(out[keys[k]]);return a},{});}""",KEYS)
    all_count=page.evaluate("""()=>{let n=0;function walk(x){if(!x?.getLayers)return;for(const y of x.getLayers()){const p=y.feature?.properties||{};if(p.id==='WH-WORLD-C0001'||p.parent_site_id==='WH-LY-002')n++;walk(y)}};for(const s of Object.values(window.__atlasTest.state))walk(s.group);return n}""")
    print("ALL_SABRATHA_FEATURES_RENDERED =", "PASS" if all_count==47 else "FAIL", all_count)
    for label,fid in KEYS.items():
        result=page.evaluate("""id=>{let f;function walk(x){if(f||!x?.getLayers)return;for(const y of x.getLayers()){if(y.feature?.properties?.id===id){f=y;return}walk(y)}};for(const s of Object.values(window.__atlasTest.state))walk(s.group);if(!f)return null;for(const s of Object.values(window.__atlasTest.state))s.group?.removeLayer?.(f);f.addTo(window.__atlasTest.map);f.openPopup();return f.feature.properties}""",fid); page.wait_for_timeout(350)
        stats=page.evaluate("""()=>{const imgs=[...document.querySelectorAll('.leaflet-popup-content img')];return {real:imgs.filter(x=>x.dataset.placeholder!=='true'&&x.naturalWidth>0).length,placeholder:imgs.filter(x=>x.dataset.placeholder==='true').length,broken:imgs.filter(x=>x.complete&&x.naturalWidth===0).length}}""")
        status="PASS" if stats["real"]>0 else "NO_CONFIRMED_IMAGE"
        print(f"SABRATHA_{label.upper()}_POPUP =",status, json.dumps(stats,ensure_ascii=False))
    print("FAILED_URLS", failed)
    print("NO_IMAGE_404 =", "PASS" if not failed else "FAIL")
    print("NO_CONSOLE_ERRORS =", "PASS" if not errors else "FAIL")
    print("FAILED =",len(failed)+len(errors))
    browser.close()
