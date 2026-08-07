import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
r=subprocess.run([sys.executable,str(root/'scripts/test-national-tourism-image-review-batch-2-playwright.py')],cwd=root,text=True,capture_output=True)
print(r.stdout,end='')
if r.stderr: print(r.stderr,end='',file=sys.stderr)
passed=r.returncode==0 and 'FAILED = 0' in r.stdout
for label in ['ATLAS_LOAD','IMAGE_POPUPS','PRIMARY_IMAGES','GALLERIES','NO_IMAGE_404','NO_CONSOLE_ERRORS','NO_PAGE_ERRORS','NO_EXTERNAL_RUNTIME_REQUESTS']:
 print(f'{label} = {"PASS" if passed else "FAIL"}')
print(f'FAILED = {0 if passed else 1}')
sys.exit(0 if passed else 1)
