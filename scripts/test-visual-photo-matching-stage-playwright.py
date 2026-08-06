import json, sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "http://localhost:8000/"
EXPECTED = {"WH-LY-003-C0001": 2, "WH-LY-003-C0016": 1, "WH-LY-003-C0022": 5, "WH-LY-003-C0023": 5, "WH-LY-003-C0021": 1, "WH-LY-005-C0004": 1}
failed = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(ROOT, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_function("typeof window.__atlasTest === 'object'")
    page.wait_for_timeout(1500)
    response = page.request.get(ROOT + "data/layers/world-heritage.geojson")
    data = json.loads(response.text())
    by_id = {f["properties"].get("id"): f["properties"] for f in data["features"]}
    for feature_id, count in EXPECTED.items():
        props = by_id.get(feature_id, {})
        images = props.get("local_images", [])
        if len(images) != count or props.get("image_count") != count or props.get("image_match_type") != "exact_feature": failed.append(feature_id + ":data")
        for image in images:
            image_response = page.request.get(ROOT + image)
            if not image_response.ok or not image_response.headers.get("content-type", "").startswith("image/"): failed.append(feature_id + ":http")
    ghadames = [p for p in by_id.values() if p.get("parent_site_id") == "WH-LY-005" and p.get("id") != "WH-LY-005-C0004"]
    if not ghadames or any(p.get("local_images") or p.get("image_count") != 0 or p.get("image_match_type") != "placeholder" for p in ghadames): failed.append("ghadames-placeholders")
    failed += errors
    browser.close()
print("CYRENE_13_CONFIRMED_IMAGES =", "PASS" if not any(x.startswith(tuple(list(EXPECTED)[:4])) for x in failed) else "FAIL")
print("ZEUS_TEMPLE_PRESERVED =", "PASS" if not any(x.startswith("WH-LY-003-C0021") for x in failed) else "FAIL")
print("AIN_AL_FARAS_PRESERVED =", "PASS" if not any(x.startswith("WH-LY-005-C0004") for x in failed) else "FAIL")
print("GHADAMES_UNCONFIRMED_PLACEHOLDERS =", "PASS" if "ghadames-placeholders" not in failed else "FAIL")
print("NO_IMAGE_HTTP_FAILURES =", "PASS" if not any(x.endswith(":http") for x in failed) else "FAIL")
print("NO_PAGE_ERRORS =", "PASS" if not errors else "FAIL")
print("FAILED =", len(failed))
if failed: print("\n".join(failed), file=sys.stderr); sys.exit(1)
