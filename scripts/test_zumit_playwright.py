from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('docs/screenshots/popup-media/zumit-after-fix.png');out.parent.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1400,'height':1000})
    page.goto('http://localhost:8080/',wait_until='domcontentloaded',timeout=60000)
    page.wait_for_function("typeof toggleLayer === 'function'")
    page.evaluate("""async()=>{const cfg=layers.find(x=>x.id==='oldTripoli');await toggleLayer(cfg,true)}""")
    page.wait_for_function("state.oldTripoli?.count>0",timeout=60000)
    page.evaluate("""()=>{const g=state.oldTripoli.group,m=g.getLayers().find(x=>String(x.getPopup?.()?.getContent?.()||'').includes('فندق زميت الأثري'));g.removeLayer(m);m.addTo(map);map.setView(m.getLatLng(),17);m.openPopup()}""")
    page.wait_for_function("document.querySelectorAll('.leaflet-popup [data-placeholder=true]').length===1",timeout=30000)
    assert page.locator('.leaflet-popup [data-placeholder=true]').count()==1
    assert page.locator('.leaflet-popup .popup-image-button').count()==1
    page.screenshot(path=str(out),full_page=False);browser.close()
print(f'Zumit fallback test passed: exactly one placeholder; screenshot {out}')
