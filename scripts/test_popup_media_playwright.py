from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080/"
OUT = Path("docs/screenshots/popup-media")
OUT.mkdir(parents=True, exist_ok=True)
LAYERS = {"heritage": "بحيرة عين الذبان", "oldTripoli": "متحف السرايا الحمراء", "hotels": "فندق كورنثيا", "akakus": "قوس أفزجار"}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    console_errors = []
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    print("goto", flush=True)
    page.goto(BASE, wait_until="domcontentloaded", timeout=45_000)
    print("dom ready", flush=True)
    page.wait_for_function("typeof map !== 'undefined' && typeof toggleLayer === 'function'", timeout=60_000)
    for layer_id, target_name in LAYERS.items():
        print(f"loading {layer_id}", flush=True)
        page.evaluate("""async id => { const cfg=layers.find(item=>item.id===id); if(!state[id]?.group) await toggleLayer(cfg,true); }""", layer_id)
        page.wait_for_function("id => state[id]?.count > 0", arg=layer_id, timeout=45_000)
        print(f"loaded {layer_id}", flush=True)
        page.evaluate("""({id,target}) => { const group=state[id].group,marker=group.getLayers().find(item => String(item.getPopup?.()?.getContent?.() || '').includes(target)); if(!marker) throw new Error(`marker not found: ${target}`); group.removeLayer(marker); marker.addTo(map); map.setView(marker.getLatLng(), 17); marker.openPopup(); }""", {"id": layer_id, "target": target_name})
        page.wait_for_function("""() => [...document.querySelectorAll('.leaflet-popup img')].some(img => img.complete && img.naturalWidth > 0 && !img.src.includes('location-placeholder'))""", timeout=30_000)
        image = page.locator(".leaflet-popup img").first
        assert image.evaluate("img => img.naturalWidth") > 0
        page.screenshot(path=str(OUT / f"{layer_id}.png"), full_page=False)
        print(f"shot {layer_id}", flush=True)
    assert not console_errors, "JavaScript errors: " + " | ".join(console_errors)
    browser.close()
print(f"Playwright popup media passed for {len(LAYERS)} layers; screenshots: {OUT}")








