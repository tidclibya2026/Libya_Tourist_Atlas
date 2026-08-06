import sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "http://localhost:8000/"
SAMPLES = {
    "CORINTHIA_POPUP": "فندق كورنثيا",
    "PENTAPOLIS_POPUP": "فندق بينثابوليس",
    "JAWAHARAT_AL_WAHA_POPUP": "فندق جوهرة الواحة",
    "TABRIS_POPUP": "فندق تبرس",
    "SHAHAT_RESORT_POPUP": "منتجع شحات السياحي",
}
results, failures, console_errors, image_404, remote_images = {}, [], [], [], []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("response", lambda response: image_404.append(response.url) if response.status == 404 and response.request.resource_type == "image" else None)
    page.on("request", lambda request: remote_images.append(request.url) if request.resource_type == "image" and "googleusercontent" in request.url else None)
    page.goto(ROOT + "?hotels-layer-test=1", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_function("typeof window.__atlasTest === 'object'")
    start = time.perf_counter()
    page.locator("input[data-id='hotels']").evaluate("(el) => { el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true})) }")
    page.wait_for_function("window.__atlasTest.state.hotels?.count === 572", timeout=60000)
    elapsed = time.perf_counter() - start
    state = page.evaluate("""() => {const s=window.__atlasTest.state.hotels; return {count:s.count, clustered:!!s.pointCluster, onMap:window.__atlasTest.map.hasLayer(s.group)}}""")
    results["HOTELS_LAYER_LOAD"] = state["count"] == 572
    results["HOTELS_FEATURE_COUNT"] = state["count"]
    results["HOTELS_CLUSTERING"] = state["clustered"]
    page.locator("input[data-id='hotels']").evaluate("(el) => { el.checked=false; el.dispatchEvent(new Event('change',{bubbles:true})) }")
    hidden = page.evaluate("!window.__atlasTest.map.hasLayer(window.__atlasTest.state.hotels.group)")
    page.locator("input[data-id='hotels']").evaluate("(el) => { el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true})) }")
    shown = page.evaluate("window.__atlasTest.map.hasLayer(window.__atlasTest.state.hotels.group)")
    results["HOTELS_TOGGLE"] = hidden and shown
    for key, target in SAMPLES.items():
        popup = page.evaluate("""target => {const state=window.__atlasTest.state.hotels;let found=null;state.pointCluster.eachLayer(layer=>{const p=layer.feature?.properties||{};if(!found&&(p.name_ar===target||p.name_ar.startsWith(target)))found=layer});if(!found)return null;state.pointCluster.removeLayer(found);found.addTo(window.__atlasTest.map);window.__atlasTest.map.setView(found.getLatLng(),15,{animate:false});found.openPopup();const container=document.createElement('div');container.innerHTML=found.getPopup()?.getContent?.()||'';return container.innerText}""", target)
        clean = bool(popup and target in popup and "null" not in popup.lower() and "undefined" not in popup.lower() and "<img" not in popup.lower() and "<![cdata[" not in popup.lower())
        results[key] = clean
    results["NO_RAW_HTML"] = all(results.get(key) for key in SAMPLES)
    results["NO_IMAGE_404"] = not image_404
    results["NO_CONSOLE_ERRORS"] = not console_errors
    results["HOTELS_INITIAL_RENDER_PERFORMANCE"] = elapsed < 10
    results["NO_EAGER_REMOTE_IMAGE_LOADING"] = not remote_images
    browser.close()
for key in ["HOTELS_LAYER_LOAD","HOTELS_TOGGLE",*SAMPLES,"NO_RAW_HTML","NO_IMAGE_404","NO_CONSOLE_ERRORS","HOTELS_CLUSTERING","HOTELS_INITIAL_RENDER_PERFORMANCE","NO_EAGER_REMOTE_IMAGE_LOADING"]:
    if not results.get(key): failures.append(key)
print("HOTELS_LAYER_LOAD =", "PASS" if results.get("HOTELS_LAYER_LOAD") else "FAIL")
print("HOTELS_FEATURE_COUNT =", results.get("HOTELS_FEATURE_COUNT", 0))
print("HOTELS_TOGGLE =", "PASS" if results.get("HOTELS_TOGGLE") else "FAIL")
for key in SAMPLES: print(f"{key} =", "PASS" if results.get(key) else "FAIL")
print("NO_RAW_HTML =", "PASS" if results.get("NO_RAW_HTML") else "FAIL")
print("NO_IMAGE_404 =", "PASS" if results.get("NO_IMAGE_404") else "FAIL")
print("NO_CONSOLE_ERRORS =", "PASS" if results.get("NO_CONSOLE_ERRORS") else "FAIL")
print("HOTELS_CLUSTERING =", "PASS" if results.get("HOTELS_CLUSTERING") else "FAIL")
print("HOTELS_INITIAL_RENDER_PERFORMANCE =", "PASS" if results.get("HOTELS_INITIAL_RENDER_PERFORMANCE") else "FAIL")
print("NO_EAGER_REMOTE_IMAGE_LOADING =", "PASS" if results.get("NO_EAGER_REMOTE_IMAGE_LOADING") else "FAIL")
print("FAILED =", len(failures))
if failures: print("\n".join(failures), file=sys.stderr); sys.exit(1)
