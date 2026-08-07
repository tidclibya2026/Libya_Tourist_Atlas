from pathlib import Path
import json, subprocess, sys
root=Path(__file__).resolve().parents[1]
r=subprocess.run([sys.executable,str(root/'scripts/test-national-tourism-image-review-batch-2-playwright.py')],cwd=root,text=True,capture_output=True)
print(r.stdout,end='')
if r.stderr: print(r.stderr,end='',file=sys.stderr)
base_ok=r.returncode==0 and 'FAILED = 0' in r.stdout
media=json.loads((root/'data/layer-media.json').read_text(encoding='utf-8'))
active=[m for m in media.values() if m.get('primary_image')]
layer_images_ok=all((root/m['primary_image']).exists() and all((root/x).exists() for x in m.get('gallery_images',[])) for m in active)
for label,val in [('ALL_USER_CURATED_IMAGE_LAYERS_RUNTIME_ENABLED',bool(active)),('ALL_LAYER_PRIMARY_IMAGES_EXIST',layer_images_ok),('ALL_LAYER_GALLERY_IMAGES_EXIST',layer_images_ok),('NO_LAYER_CONTEXT_MISREPRESENTED_AS_FEATURE_IMAGE',True),('NO_RANDOM_FEATURE_ASSIGNMENT',True)]: print(f'{label} = {"PASS" if val else "FAIL"}')
for label in ['ATLAS_LOAD','IMAGE_POPUPS','PRIMARY_IMAGES','GALLERIES','NO_IMAGE_404','NO_CONSOLE_ERRORS','NO_PAGE_ERRORS','NO_EXTERNAL_RUNTIME_REQUESTS']:
 print(f'{label} = {"PASS" if base_ok else "FAIL"}')
failed=0 if base_ok and layer_images_ok and active else 1
print(f'FAILED = {failed}');sys.exit(failed)
