from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/?theatre-actual-test=1"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    failed = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("requestfailed", lambda request: failed.append(request.url))
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_function("typeof window.__atlasTest === 'object'")
    page.wait_for_timeout(800)
    clicked_id = page.evaluate("""() => {
      let found;
      function walk(layer) {
        if (found || !layer?.getLayers) return;
        for (const child of layer.getLayers()) {
          const properties = child.feature?.properties || {};
          if (properties.name_ar === 'المسرح') { found = child; return; }
          walk(child);
        }
      }
      for (const state of Object.values(window.__atlasTest.state)) walk(state.group);
      if (!found) return null;
      for (const state of Object.values(window.__atlasTest.state)) state.group?.removeLayer?.(found);
      found.addTo(window.__atlasTest.map);
      found.openPopup();
      return found.feature?.properties?.id || null;
    }""")
    page.wait_for_timeout(700)
    stats = page.evaluate("""() => {
      const images = [...document.querySelectorAll('.leaflet-popup-content img')];
      return {
        real: images.filter(image => image.dataset.placeholder !== 'true' && image.naturalWidth > 0).length,
        placeholder: images.filter(image => image.dataset.placeholder === 'true').length,
        broken: images.filter(image => image.complete && image.naturalWidth === 0).length
      };
    }""")
    assert clicked_id == 'WH-LY-001-0026', clicked_id
    assert stats['real'] > 0 and stats['broken'] == 0
    assert stats['placeholder'] == 0
    assert not failed, failed
    assert not errors, errors
    print('THEATRE_CLICKED_FEATURE_ID =', clicked_id)
    print('THEATRE_POPUP_REAL_IMAGE = PASS')
    print('THEATRE_NOT_PLACEHOLDER = PASS')
    print('NO_IMAGE_404 = PASS')
    print('NO_CONSOLE_ERRORS = PASS')
    print('FAILED = 0')
    browser.close()
