import csv, os
from PIL import Image
root=os.getcwd();rows=list(csv.DictReader(open('docs/media-recovery-success.csv',encoding='utf-8-sig')));files={r['final_local_path'] for r in rows if r['final_local_path']};failed=[]
for rel in sorted(files):
    full=os.path.join(root,*rel.lstrip('/').split('/'))
    try:
        if os.path.getsize(full)<=1024: raise ValueError('file <= 1KB')
        with Image.open(full) as im: im.verify()
        with Image.open(full) as im: im.load()
    except Exception as e: failed.append((rel,str(e)))
print(f'Pillow verified {len(files)-len(failed)}/{len(files)} unique recovered files')
if failed:
    for item in failed[:30]: print(item)
    raise SystemExit(1)
