import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")


TARGET_AR = "آثار قورينا"


def find_feature(page):
    return page.evaluate(
        """
        () => {
          let found = null;
          function walk(layer) {
            if (found || !layer?.getLayers) return;
            for (const child of layer.getLayers()) {
              const p = child.feature?.properties || {};
              if (p.name_ar === 'آثار قورينا' || p.name_ar === 'أثار قورينا' ||
                  p.name_en === 'The Ruins of Cyrene' || p.name_en === 'The ruins of Cyrene') {
                found = child; return;
              }
              walk(child);
            }
          }
          for (const state of Object.values(window.__atlasTest.state || {})) walk(state.group);
          if (!found) return null;
          for (const state of Object.values(window.__atlasTest.state || {})) state.group?.removeLayer?.(found);
          found.addTo(window.__atlasTest.map);
          found.fire('click');
          return found.feature?.properties || null;
        }
        """
    )


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors, failed = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("requestfailed", lambda request: failed.append(request.url))
    page.goto("http://localhost:8000/?cyrene-clicked-feature-test=1", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_function("typeof window.__atlasTest==='object'")
    page.wait_for_timeout(800)
    props = find_feature(page)
    page.wait_for_timeout(700)
    title = page.locator(".popup-title").inner_text() if page.locator(".popup-title").count() else ""
    state = page.evaluate(
        """
        () => {
          const images = [...document.querySelectorAll('.leaflet-popup-content img')];
          const text = document.querySelector('.leaflet-popup-content')?.innerText || '';
          return {text, images: images.map(i => ({src:i.currentSrc || i.src, placeholder:i.dataset.placeholder === 'true', width:i.naturalWidth, height:i.naturalHeight}))};
        }
        """
    )
    real = [i for i in state["images"] if not i["placeholder"] and i["width"] > 0 and i["height"] > 0]
    coordinate_text = lambda value: any(token in (value or "") for token in ("21.85", "32.82", "x:", "y:"))
    data_ok = bool(props and title == TARGET_AR and props.get("category") == "مواقع التراث العالمي"
                   and props.get("subcategory") == "موقع أثري"
                   and props.get("description_ar") and not coordinate_text(props.get("description_ar"))
                   and props.get("local_images") and props.get("image_count") == len(props["local_images"])
                   and not coordinate_text(props.get("category")))
    print("CYRENE_ACTUAL_CLICKED_FEATURE_ID =", props.get("id") if props else "MISSING")
    print("CYRENE_POPUP_TITLE =", title)
    print("CYRENE_POPUP_IMAGE_SRC =", real[0]["src"] if real else "")
    print("CYRENE_POPUP_IS_PLACEHOLDER =", "false" if real else "true")
    print("CYRENE_POPUP_LOCAL_IMAGES_COUNT =", len(props.get("local_images", [])) if props else 0)
    print("CYRENE_CLICKED_FEATURE_DATA =", "PASS" if data_ok else "FAIL")
    print("CYRENE_CLICKED_FEATURE_REAL_IMAGE =", "PASS" if real else "FAIL")
    print("CYRENE_CLICKED_FEATURE_NOT_PLACEHOLDER =", "PASS" if real and not any(i["placeholder"] for i in real) else "FAIL")
    print("CYRENE_IMAGE_HTTP =", "PASS" if real and not failed else "FAIL")
    print("NO_IMAGE_404 =", "PASS" if not failed else "FAIL")
    print("NO_CONSOLE_ERRORS =", "PASS" if not errors else "FAIL")
    print("FAILED =", len(failed) + len(errors))
    browser.close()
