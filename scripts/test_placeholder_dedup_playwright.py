from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(headless=True);page=b.new_page();page.goto('http://localhost:8080/',wait_until='domcontentloaded',timeout=60000);page.wait_for_function("typeof toggleLayer==='function'")
    page.evaluate("""async()=>{await toggleLayer(layers.find(x=>x.id==='oldTripoli'),true)}""");page.wait_for_function("state.oldTripoli?.count>0",timeout=60000)
    for _ in range(3):
        page.evaluate("""()=>{const g=state.oldTripoli.group,m=g.getLayers().find(x=>String(x.getPopup?.()?.getContent?.()||'').includes('فندق زميت الأثري'));g.removeLayer(m);m.addTo(map);map.setView(m.getLatLng(),17);m.closePopup();m.openPopup()}""")
        page.wait_for_function("document.querySelectorAll('.leaflet-popup [data-placeholder=true]').length===1",timeout=30000)
        assert page.locator('.leaflet-popup [data-placeholder=true]').count()==1
        assert page.locator('.leaflet-popup .popup-image-button').count()==1
    b.close()
print('Placeholder deduplication passed across three popup reopen cycles.')
