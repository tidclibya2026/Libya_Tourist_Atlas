import sys, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "http://127.0.0.1:8765/"
SAMPLES = {
    "BROWN_RESTAURANT_POPUP": "مطعم براون للوجبات السريعة",
    "AL_NIBRAS_POPUP": "مطعم النبراس",
    "LA_RAMBLAA_POPUP": "مطعم لارمبلا",
    "FATTOUSH_POPUP": "مطعم فتوش للمأكولات اللبنانية حي الأندلس",
    "AL_ROBYAN_POPUP": "مطعم الروبيان للمأكولات البحرية",
}
results, failures, console_errors, image_404, remote_images = {}, [], [], [], []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("response", lambda response: image_404.append(response.url) if response.status == 404 and response.request.resource_type == "image" else None)
    page.on("request", lambda request: remote_images.append(request.url) if request.resource_type == "image" and ("googleusercontent" in request.url or "mymaps.usercontent.google.com" in request.url) else None)
    page.goto(ROOT + "?tripoli-restaurants-layer-test=1", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_function("typeof window.__atlasTest === 'object'")
    start = time.perf_counter()
    page.locator("input[data-id='tripoliRestaurants']").evaluate("(el) => { el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true})) }")
    page.wait_for_function("window.__atlasTest.state.tripoliRestaurants?.count === 75", timeout=60000)
    elapsed = time.perf_counter() - start
    state = page.evaluate("""() => {const s=window.__atlasTest.state.tripoliRestaurants; return {count:s.count, clustered:!!s.pointCluster, onMap:window.__atlasTest.map.hasLayer(s.group)}}""")
    results["RESTAURANTS_LAYER_LOAD"] = state["count"] == 75
    results["RESTAURANTS_FEATURE_COUNT"] = state["count"]
    results["RESTAURANTS_CLUSTERING"] = state["clustered"]
    page.locator("input[data-id='tripoliRestaurants']").evaluate("(el) => { el.checked=false; el.dispatchEvent(new Event('change',{bubbles:true})) }")
    hidden = page.evaluate("!window.__atlasTest.map.hasLayer(window.__atlasTest.state.tripoliRestaurants.group)")
    page.locator("input[data-id='tripoliRestaurants']").evaluate("(el) => { el.checked=true; el.dispatchEvent(new Event('change',{bubbles:true})) }")
    shown = page.evaluate("window.__atlasTest.map.hasLayer(window.__atlasTest.state.tripoliRestaurants.group)")
    results["RESTAURANTS_TOGGLE"] = hidden and shown
    for key, target in SAMPLES.items():
        popup = page.evaluate("""target => {const state=window.__atlasTest.state.tripoliRestaurants;let found=null;state.pointCluster.eachLayer(layer=>{const p=layer.feature?.properties||{};if(!found&&p.name_ar===target)found=layer});if(!found)return null;state.pointCluster.removeLayer(found);found.addTo(window.__atlasTest.map);found.openPopup();const container=document.createElement('div');container.innerHTML=found.getPopup()?.getContent?.()||'';return container.innerText}""", target)
        results[key] = bool(popup and target in popup and "null" not in popup.lower() and "undefined" not in popup.lower() and "<img" not in popup.lower() and "<![cdata[" not in popup.lower())
    results["NO_RAW_HTML"] = all(results.get(key) for key in SAMPLES)
    results["NO_IMAGE_404"] = not image_404
    results["NO_CONSOLE_ERRORS"] = not console_errors
    results["RESTAURANTS_INITIAL_RENDER_PERFORMANCE"] = elapsed < 10
    results["NO_EAGER_REMOTE_IMAGE_LOADING"] = not remote_images
    browser.close()
for key in ["RESTAURANTS_LAYER_LOAD","RESTAURANTS_TOGGLE","RESTAURANTS_CLUSTERING",*SAMPLES,"NO_RAW_HTML","NO_IMAGE_404","NO_CONSOLE_ERRORS","RESTAURANTS_INITIAL_RENDER_PERFORMANCE","NO_EAGER_REMOTE_IMAGE_LOADING"]:
    if not results.get(key): failures.append(key)
print("RESTAURANTS_LAYER_LOAD =", "PASS" if results.get("RESTAURANTS_LAYER_LOAD") else "FAIL")
print("RESTAURANTS_FEATURE_COUNT =", results.get("RESTAURANTS_FEATURE_COUNT", 0))
print("RESTAURANTS_TOGGLE =", "PASS" if results.get("RESTAURANTS_TOGGLE") else "FAIL")
print("RESTAURANTS_CLUSTERING =", "PASS" if results.get("RESTAURANTS_CLUSTERING") else "FAIL")
for key in SAMPLES: print(f"{key} =", "PASS" if results.get(key) else "FAIL")
print("NO_RAW_HTML =", "PASS" if results.get("NO_RAW_HTML") else "FAIL")
print("NO_IMAGE_404 =", "PASS" if results.get("NO_IMAGE_404") else "FAIL")
print("NO_CONSOLE_ERRORS =", "PASS" if results.get("NO_CONSOLE_ERRORS") else "FAIL")
print("RESTAURANTS_INITIAL_RENDER_PERFORMANCE =", "PASS" if results.get("RESTAURANTS_INITIAL_RENDER_PERFORMANCE") else "FAIL")
print("NO_EAGER_REMOTE_IMAGE_LOADING =", "PASS" if results.get("NO_EAGER_REMOTE_IMAGE_LOADING") else "FAIL")
print("FAILED =", len(failures))
if failures: print("\n".join(failures), file=sys.stderr); sys.exit(1)
