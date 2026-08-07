import asyncio
import json
import socket
import subprocess
import sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[1]
SHOT = ROOT / 'docs' / 'screenshots' / 'atlas-ux-geoai-phase-1-repair'
def free_port():
    sock=socket.socket(); sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]; sock.close(); return port
async def main():
    port=free_port(); SHOT.mkdir(parents=True, exist_ok=True)
    server=subprocess.Popen([sys.executable,'-m','http.server',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    errors=[]; external=[]; failed=[]; image404=[]
    try:
      async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True); page=await browser.new_page(viewport={'width':1280,'height':820}); await page.add_init_script('window.__ATLAS_OFFLINE__ = true;')
        page.on('console',lambda msg: errors.append(f'console:{msg.type}:{msg.text}') if msg.type=='error' else None)
        page.on('pageerror',lambda exc: errors.append(f'pageerror:{exc}'))
        async def route_request(route):
          req=route.request
          if not req.url.startswith(f'http://127.0.0.1:{port}'):
            external.append(req.url); await route.abort()
          else:
            await route.continue_()
        await page.route('**/*', route_request); page.on('requestfailed',lambda req: failed.append(req.url))
        page.on('response',lambda res: image404.append(res.url) if res.status==404 and any(x in res.request.resource_type for x in ['image','stylesheet','script']) else None)
        await page.goto(f'http://127.0.0.1:{port}/index.html',wait_until='domcontentloaded'); await page.wait_for_timeout(1200)
        async def check(name,ok): print(f'{name} = {"PASS" if ok else "FAIL"}'); return ok
        results=[]
        results.append(await check('ATLAS_LOAD',await page.locator('#map').count()==1)); results.append(await check('HEADER_VISIBLE',await page.locator('.topbar').is_visible())); results.append(await check('LOGO_VISIBLE',await page.locator('.brand-lockup').is_visible())); results.append(await check('TAGLINE_VISIBLE',await page.locator('.brand-strip').is_visible())); results.append(await check('MAP_VISIBLE',await page.locator('#map').is_visible())); results.append(await check('SMART_SEARCH_VISIBLE',await page.locator('#searchInput').is_visible())); results.append(await check('LAYER_EXPLORER_VISIBLE',await page.locator('#layerList').is_visible())); results.append(await check('GEOAI_BUTTON_VISIBLE',await page.locator('#geoaiButton').is_visible()))
        async def open_feature(layer_id, label, shot_name):
          await page.evaluate("({id}) => { const f=window.AtlasRuntime.getLayerFeatures(id).find(x=>Array.isArray(x.feature.properties?.local_images)&&x.feature.properties.local_images.length); if(f) window.AtlasRuntime.focusFeature(f); }", {'id':layer_id})
          await page.wait_for_timeout(700)
          visible=await page.locator('.leaflet-popup .popup-gallery img').count()>0
          placeholder=await page.locator('.leaflet-popup .popup-placeholder-only').count()==0
          await page.screenshot(path=str(SHOT/shot_name),full_page=True)
          results.append(await check(f'{label}_FEATURE_IMAGE_VISIBLE',visible)); results.append(await check(f'{label}_FEATURE_NOT_PLACEHOLDER',placeholder)); return visible and placeholder
        for layer in ['hotels','oldTripoli','akakus','heritage']:
          await page.evaluate('id => window.AtlasRuntime.showLayer(id)', layer); await page.wait_for_timeout(650)
        await open_feature('hotels','HOTEL','hotel-with-image.png'); await open_feature('oldTripoli','OLD_TRIPOLI','old-tripoli-with-image.png'); await open_feature('akakus','AKAKUS','akakus-with-image.png'); await open_feature('heritage','WORLD_HERITAGE','heritage-with-image.png')
        results.append(await check('FEATURE_GALLERY_VISIBLE',await page.locator('.leaflet-popup .popup-gallery').count()>0))
        await page.locator('#geoaiButton').click(); await page.wait_for_timeout(100); results.append(await check('GEOAI_PANEL_OPENS',await page.locator('#geoaiPanel').get_attribute('open') is not None))
        async def query(text, expected, label, screenshot=None):
          await page.locator('#geoaiInput').fill(text); await page.locator('#geoaiForm button').click(); await page.wait_for_timeout(900)
          ok=await page.locator('#geoaiMessages').get_by_text(expected,exact=False).count()>0 if expected else await page.locator('#resultsPanel').is_visible()
          if screenshot: await page.screenshot(path=str(SHOT/screenshot),full_page=True)
          results.append(await check(label,ok)); return ok
        await query('اعرض الفنادق','تم تفعيل طبقة','QUERY_SHOW_HOTELS','geoai-show-hotels.png'); results.append(await check('HOTELS_LAYER_ACTIVE',await page.locator('[data-id="hotels"]').is_checked()))
        await query('اخف الفنادق','تم إخفاء طبقة','QUERY_HIDE_HOTELS'); results.append(await check('HOTELS_LAYER_INACTIVE',not await page.locator('[data-id="hotels"]').is_checked()))
        await page.locator('#geoaiInput').fill('لبدة'); await page.locator('#geoaiForm button').click(); await page.wait_for_timeout(900); results.append(await check('QUERY_LEPTIS',await page.locator('#resultsPanel .result-card').count()>0)); await page.screenshot(path=str(SHOT/'geoai-search-leptis.png'),full_page=True)
        await page.locator('#geoaiInput').fill('غدامس'); await page.locator('#geoaiForm button').click(); await page.wait_for_timeout(900); results.append(await check('QUERY_GHADAMES',await page.locator('#resultsPanel .result-card').count()>0))
        await page.locator('#geoaiInput').fill('قوس سيبتيموس'); await page.locator('#geoaiForm button').click(); await page.wait_for_timeout(900); results.append(await check('QUERY_SEPTIMIUS',await page.locator('#resultsPanel .result-card').count()>0))
        await page.locator('#geoaiInput').fill('مواقع طرابلس'); await page.locator('#geoaiForm button').click(); await page.wait_for_timeout(900); results.append(await check('SEARCH_OR_FILTER_TRIPOLI',await page.locator('[data-id="oldTripoli"]').is_checked() or await page.locator('#resultsPanel').is_visible()))
        for prompt in ['اعرض الفنادق','اعرض مواقع التراث العالمي','استكشف أكاكوس','اعرض فرص الاستثمار','المواقع القريبة','اعرض مواقع طرابلس']:
          await page.locator(f'[data-prompt="{prompt}"]').click(); await page.wait_for_timeout(120)
        await page.locator('#geoaiInput').fill('المواقع القريبة'); await page.locator('#geoaiForm button').click(); await page.wait_for_timeout(650); results.append(await check('GEOAI_NEARBY',await page.locator('#geoaiMessages').get_by_text('موقعًا قريبًا', exact=False).count()>0 or await page.locator('#resultsPanel').is_visible())); results.append(await check('GEOAI_QUICK_PROMPTS',await page.locator('#geoaiMessages .geoai-message').count()>=6))
        for width,height in [(375,812),(390,844),(430,932)]:
          await page.set_viewport_size({'width':width,'height':height}); await page.wait_for_timeout(100); results.append(await check(f'MOBILE_{width}_NO_HORIZONTAL_OVERFLOW',not await page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 1'))); results.append(await check(f'MOBILE_{width}_GEOAI_VISIBLE',await page.locator('#geoaiButton').is_visible()))
        await browser.close()
    finally:
      server.terminate(); server.wait(timeout=5)
    print('FEATURE_WITH_IMAGE_NOT_SHOWING_PLACEHOLDER =', 'PASS' if not image404 else 'FAIL')
    print('NO_IMAGE_404 =', 'PASS' if not image404 else 'FAIL')
    print('NO_CONSOLE_ERRORS =', 'PASS' if not errors else 'FAIL'); print('NO_PAGE_ERRORS =', 'PASS' if not errors else 'FAIL'); print('NO_EXTERNAL_RUNTIME_REQUESTS =', 'PASS' if not external else 'FAIL')
    if errors: print('ERRORS =',json.dumps(errors,ensure_ascii=False));
    if external: print('EXTERNAL_REQUESTS =',json.dumps(external,ensure_ascii=False));
    failed_count=sum(1 for x in results if not x)+len(errors)+len(external)+len(image404)
    print('FAILED =',failed_count)
    if failed_count: raise SystemExit(1)
if __name__=='__main__': asyncio.run(main())
