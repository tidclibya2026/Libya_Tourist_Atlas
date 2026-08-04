from pathlib import Path
from playwright.sync_api import sync_playwright
OUT=Path('docs/screenshots/media-recovery');OUT.mkdir(parents=True,exist_ok=True)
LAYERS=['akakus','oldTripoli','hotels','heritage','resorts','investment']
with sync_playwright() as p:
    b=p.chromium.launch(headless=True);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://localhost:8080/',wait_until='domcontentloaded',timeout=60000);page.wait_for_function("typeof window.__atlasTest==='object'")
    for layer in LAYERS:
        page.evaluate("""async id=>{const cfg=window.__atlasTest.layers.find(x=>x.id===id);if(!window.__atlasTest.state[id]?.group)await toggleLayer(cfg,true)}""",layer);page.wait_for_function("id=>window.__atlasTest.state[id]?.count>0",arg=layer,timeout=120000)
        available=page.evaluate("""id=>window.__atlasTest.state[id].group.getLayers().filter(m=>String(m.getPopup?.()?.getContent?.()||'').split('<div class="popup-body">')[0].includes('data-image="http://localhost:8080/assets/images/')).length""",layer);assert available>0,f'{layer}: no localized markers'
        tested=min(10,available)
        for i in range(tested):
            page.evaluate("""({id,i})=>{const g=window.__atlasTest.state[id].group,c=g.getLayers().filter(m=>String(m.getPopup?.()?.getContent?.()||'').split('<div class="popup-body">')[0].includes('data-image="http://localhost:8080/assets/images/')),m=c[i];window.__tested=m;g.removeLayer(m);m.addTo(window.__atlasTest.map);window.__atlasTest.map.closePopup();window.__atlasTest.map.setView(m.getLatLng(),17);m.openPopup()}""",{'id':layer,'i':i})
            page.wait_for_function("""()=>{const roots=[...document.querySelectorAll('.leaflet-popup-content')],root=roots[roots.length-1],imgs=root?[...root.querySelectorAll(':scope > .tourism-popup > .popup-gallery > .popup-image-button > img')]:[];return imgs.length>0&&imgs.every(x=>x.complete)}""",timeout=30000)
            result=page.evaluate("""()=>{const roots=[...document.querySelectorAll('.leaflet-popup-content')],root=roots[roots.length-1],imgs=root?[...root.querySelectorAll(':scope > .tourism-popup > .popup-gallery > .popup-image-button > img')]:[],local=imgs.some(x=>x.src.includes('/assets/images/'));return{count:imgs.length,broken:imgs.filter(x=>x.naturalWidth<=0).length,placeholders:imgs.filter(x=>x.dataset.placeholder==='true').length,google:local?imgs.filter(x=>/googleusercontent|mymaps/.test(new URL(x.src).hostname)).length:0}}""")
            assert result['broken']==0,(layer,i,result);assert result['placeholders']<=1,(layer,i,result);assert result['google']==0,(layer,i,result)
            if i==0:page.screenshot(path=str(OUT/f'{layer}.png'),full_page=False)
            page.evaluate("""id=>{const m=window.__tested;window.__atlasTest.map.closePopup();m.closePopup();window.__atlasTest.map.removeLayer(m);window.__atlasTest.state[id].group.addLayer(m)}""",layer)
        print(f'{layer}: {tested} localized popups passed')
    page.evaluate("""()=>{const g=window.__atlasTest.state.oldTripoli.group,m=g.getLayers().find(x=>String(x.getPopup?.()?.getContent?.()||'').includes('فندق زميت الأثري'));g.removeLayer(m);m.addTo(window.__atlasTest.map);window.__atlasTest.map.closePopup();window.__atlasTest.map.setView(m.getLatLng(),17);m.openPopup()}""");page.wait_for_function("""()=>[...document.querySelectorAll('.leaflet-popup-content > .tourism-popup > .popup-gallery > .popup-image-button > img')].length===3&&[...document.querySelectorAll('.leaflet-popup-content > .tourism-popup > .popup-gallery > .popup-image-button > img')].every(x=>x.complete&&x.naturalWidth>0&&x.src.includes('/assets/images/'))""",timeout=30000);page.screenshot(path=str(OUT/'zumit-recovered.png'),full_page=False)
    assert not errors,' | '.join(errors);b.close()
print(f'Recovered media Playwright passed; screenshots: {OUT}')

















