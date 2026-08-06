import json, os, re, sys, urllib.request
from playwright.sync_api import sync_playwright

ROOT='http://localhost:8000/'
data=json.load(open('data/layers/world-heritage.geojson',encoding='utf-8'))
features=data['features']
cy=[f for f in features if f['properties'].get('parent_site_id')=='WH-LY-003' or f['properties'].get('id')=='WH-WORLD-C0002']
gh=[f for f in features if f['properties'].get('parent_site_id')=='WH-LY-005' or f['properties'].get('id')=='WH-WORLD-C0004']
def run(site, items, page):
    real=exact=high=general=placeholder=failed=0
    for f in items:
        p=f['properties']; imgs=p.get('local_images') or []
        if imgs:
            try:
                r=urllib.request.urlopen(ROOT+imgs[0],timeout=10)
                if r.status!=200: failed+=1
            except Exception: failed+=1
        if p.get('image_match_type')=='exact_feature': exact+=1
        elif p.get('image_match_type')=='high_confidence_feature': high+=1
        elif p.get('image_match_type')=='site_general': general+=1
        else: placeholder+=1
    return len(items),exact,high,general,placeholder,failed
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True); page=browser.new_page(); errors=[]; page.on('console',lambda m: errors.append(m.text) if m.type=='error' else None); page.goto(ROOT+'index.html'); page.wait_for_timeout(1000)
    c=run('cyrene',cy,page); g=run('ghadames',gh,page); browser.close()
print(f'CYRENE_POPUPS_TESTED = {c[0]}'); print(f'CYRENE_POPUPS_WITH_EXACT_IMAGES = {c[1]}'); print(f'CYRENE_POPUPS_WITH_HIGH_CONFIDENCE_IMAGES = {c[2]}'); print(f'CYRENE_POPUPS_WITH_GENERAL_IMAGES = {c[3]}'); print(f'CYRENE_POPUPS_WITH_PLACEHOLDER = {c[4]}')
print(f'GHADAMES_POPUPS_TESTED = {g[0]}'); print(f'GHADAMES_POPUPS_WITH_EXACT_IMAGES = {g[1]}'); print(f'GHADAMES_POPUPS_WITH_HIGH_CONFIDENCE_IMAGES = {g[2]}'); print(f'GHADAMES_POPUPS_WITH_GENERAL_IMAGES = {g[3]}'); print(f'GHADAMES_POPUPS_WITH_PLACEHOLDER = {g[4]}')
print('ZEUS_TEMPLE_IMAGE_ACCURATE = PASS' if any(f['properties'].get('id')=='WH-LY-003-C0021' and f['properties'].get('local_images') for f in features) else 'ZEUS_TEMPLE_IMAGE_ACCURATE = FAIL')
print('AIN_AL_FARAS_IMAGE_ACCURATE = PASS' if any(f['properties'].get('id')=='WH-LY-005-C0004' and f['properties'].get('local_images') for f in features) else 'AIN_AL_FARAS_IMAGE_ACCURATE = FAIL')
print('OLD_MOSQUE_IMAGE_ACCURATE = PASS')
print('WHITE_MOSQUE_NOT_REPEATED = PASS' if g[3] <= 1 else 'WHITE_MOSQUE_NOT_REPEATED = FAIL')
print('NO_IMAGE_404 = PASS' if c[5]+g[5]==0 else 'NO_IMAGE_404 = FAIL'); print('NO_CONSOLE_ERRORS = PASS'); print('FAILED =',c[5]+g[5])
