import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8'); ROOT='http://127.0.0.1:8766/'; PROJECT=Path(__file__).resolve().parents[1]
features=json.loads((PROJECT/'data/layers/tourist-villages-resorts.geojson').read_text(encoding='utf-8'))['features']; chosen=[]; seen_types=set(); seen_regions=set()
for f in features:
 p=f['properties']; typ=p['facility_type_code']; region=p.get('region_ar') or p.get('city_ar') or 'غير محدد'
 if len(chosen)<5 and (typ not in seen_types or region not in seen_regions): chosen.append(p['name_ar']); seen_types.add(typ); seen_regions.add(region)
 if len(chosen)==5: break
failures=[]; results={}; console_errors=[]; image_404=[]; remote=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True); page=browser.new_page(viewport={'width':1440,'height':1000}); page.on('console',lambda m:console_errors.append(m.text) if m.type=='error' else None); page.on('response',lambda r:image_404.append(r.url) if r.status==404 and r.request.resource_type=='image' else None); page.on('request',lambda r:remote.append(r.url) if r.resource_type=='image' and ('googleusercontent' in r.url or 'mymaps.usercontent.google.com' in r.url) else None)
 page.goto(ROOT+'?resorts-layer-test=1',wait_until='domcontentloaded',timeout=60000); page.wait_for_function("typeof window.__atlasTest === 'object'"); start=time.perf_counter(); page.locator("input[data-id='resorts']").evaluate("el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}"); page.wait_for_function("window.__atlasTest.state.resorts?.count === 262",timeout=60000); elapsed=time.perf_counter()-start; state=page.evaluate("()=>{const s=window.__atlasTest.state.resorts;return{count:s.count,clustered:!!s.pointCluster}}"); results['RESORTS_LAYER_LOAD']=state['count']==262; results['RESORTS_FEATURE_COUNT']=state['count']; results['RESORTS_CLUSTERING']=state['clustered']
 page.locator("input[data-id='resorts']").evaluate("el=>{el.checked=false;el.dispatchEvent(new Event('change',{bubbles:true}))}"); hidden=page.evaluate("!window.__atlasTest.map.hasLayer(window.__atlasTest.state.resorts.group)"); page.locator("input[data-id='resorts']").evaluate("el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}"); shown=page.evaluate("window.__atlasTest.map.hasLayer(window.__atlasTest.state.resorts.group)"); results['RESORTS_TOGGLE']=hidden and shown
 for i,target in enumerate(chosen,1):
  popup=page.evaluate("""target=>{const s=window.__atlasTest.state.resorts;let found=null;s.pointCluster.eachLayer(l=>{if(!found&&l.feature?.properties?.name_ar===target)found=l});if(!found)return null;s.pointCluster.removeLayer(found);found.addTo(window.__atlasTest.map);found.openPopup();const d=document.createElement('div');d.innerHTML=found.getPopup()?.getContent?.()||'';return d.innerText}""",target); results[f'RESORT_SAMPLE_{i}_POPUP']=bool(popup and target in popup and 'null' not in popup.lower() and 'undefined' not in popup.lower() and '<![cdata[' not in popup.lower())
 results['NO_RAW_HTML']=all(results.get(f'RESORT_SAMPLE_{i}_POPUP') for i in range(1,6)); results['NO_EAGER_REMOTE_IMAGE_LOADING']=not remote; results['NO_IMAGE_404']=not image_404; results['NO_CONSOLE_ERRORS']=not console_errors; results['RESORTS_INITIAL_RENDER_PERFORMANCE']=elapsed<10; browser.close()
for key in ['RESORTS_LAYER_LOAD','RESORTS_TOGGLE','RESORTS_CLUSTERING',*[f'RESORT_SAMPLE_{i}_POPUP' for i in range(1,6)],'NO_RAW_HTML','NO_EAGER_REMOTE_IMAGE_LOADING','NO_IMAGE_404','NO_CONSOLE_ERRORS','RESORTS_INITIAL_RENDER_PERFORMANCE']:
 if not results.get(key): failures.append(key)
print('RESORTS_LAYER_LOAD =','PASS' if results.get('RESORTS_LAYER_LOAD') else 'FAIL'); print('RESORTS_FEATURE_COUNT =',results.get('RESORTS_FEATURE_COUNT',0)); print('RESORTS_TOGGLE =','PASS' if results.get('RESORTS_TOGGLE') else 'FAIL'); print('RESORTS_CLUSTERING =','PASS' if results.get('RESORTS_CLUSTERING') else 'FAIL')
for i in range(1,6): print(f'RESORT_SAMPLE_{i}_POPUP =','PASS' if results.get(f'RESORT_SAMPLE_{i}_POPUP') else 'FAIL')
for key in ['NO_RAW_HTML','NO_EAGER_REMOTE_IMAGE_LOADING','NO_IMAGE_404','NO_CONSOLE_ERRORS','RESORTS_INITIAL_RENDER_PERFORMANCE']: print(f'{key} =','PASS' if results.get(key) else 'FAIL')
print('FAILED =',len(failures));
if failures: print('\n'.join(failures),file=sys.stderr); sys.exit(1)
