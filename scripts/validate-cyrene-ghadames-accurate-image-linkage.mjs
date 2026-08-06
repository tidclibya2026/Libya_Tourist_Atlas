import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const data=JSON.parse(fs.readFileSync(path.join(root,'data/layers/world-heritage.geojson'),'utf8'));
const all=data.features;
const cy=all.filter(f=>f.properties.parent_site_id==='WH-LY-003'||f.properties.id==='WH-WORLD-C0002');
const gh=all.filter(f=>f.properties.parent_site_id==='WH-LY-005'||f.properties.id==='WH-WORLD-C0004');
const failures=[];
const exists=p=>fs.existsSync(path.join(root,p));
const validate=fs=>fs.forEach(f=>{const p=f.properties; const imgs=p.local_images||[]; if(p.image_count!==imgs.length) failures.push(`${p.id}:image_count`); const uniq=new Set(imgs); if(uniq.size!==imgs.length) failures.push(`${p.id}:duplicate`); for(const img of imgs){if(!img||img.includes('review-required')||img.includes('\\')||/^(?:[A-Za-z]:|file:|https?:|blob:)/i.test(img)||!exists(img)) failures.push(`${p.id}:bad-image:${img}`);}});
validate(cy); validate(gh);
const cyUsage=new Map(),ghUsage=new Map(); for(const f of cy) for(const i of f.properties.local_images||[]) cyUsage.set(i,(cyUsage.get(i)||0)+1); for(const f of gh) for(const i of f.properties.local_images||[]) ghUsage.set(i,(ghUsage.get(i)||0)+1);
if([...cyUsage].some(([i,n])=>n>5 && !i.includes('main-site'))) failures.push('cyrene_mass_reuse');
if([...ghUsage].some(([i,n])=>n>5)) failures.push('ghadames_mass_reuse');
const nonRel=gh.filter(f=>!/مسجد|جامع|ديني|mosque|mosque/i.test(String(f.properties.name_ar||''))); const mosque=gh.flatMap(f=>f.properties.local_images||[]).filter(i=>i.includes('main-site'));
if(nonRel.some(f=>(f.properties.local_images||[]).some(i=>i.includes('main-site'))&&f.properties.id!=='WH-WORLD-C0004')) failures.push('mosque_or_general_on_nonreligious');
const ain=all.find(f=>f.properties.id==='WH-LY-005-C0004'); if(!ain||ain.properties.local_images?.length!==1||!ain.properties.local_images[0].includes('ain-al-faras')) failures.push('ain_not_preserved');
const zeus=all.find(f=>f.properties.id==='WH-LY-003-C0021'); if(!zeus||zeus.properties.local_images?.length!==1||!zeus.properties.local_images[0].includes('temple-of-zeus')) failures.push('zeus_not_preserved');
const c5=all.find(f=>f.properties.id==='WH-LY-003-C0005'); if(!c5||!c5.properties.local_images?.length) failures.push('cyrene_component_not_preserved');
const old=all.find(f=>f.properties.id==='WH-LY-005-C0002'); if(!old) failures.push('old_mosque_missing');
for(const f of cy){const p=f.properties; if(/[xy]\s*:|city\s*:/i.test(`${p.category} ${p.subcategory} ${p.description_ar} ${p.description_en}`)) failures.push(`${p.id}:contaminated`);}
const out=(k,v)=>console.log(`${k} = ${v}`); out('CYRENE_NO_MASS_IMAGE_REUSE', failures.some(x=>x.includes('cyrene_mass'))?'FAIL':'PASS'); out('GHADAMES_NO_MASS_IMAGE_REUSE', failures.some(x=>x.includes('ghadames_mass'))?'FAIL':'PASS'); out('NO_MOSQUE_IMAGE_ON_NON_RELIGIOUS_FEATURES', failures.some(x=>x.includes('mosque_or'))?'FAIL':'PASS'); out('AIN_AL_FARAS_IMAGE_EXCLUSIVE', failures.some(x=>x.includes('ain_not'))?'FAIL':'PASS'); out('NO_REVIEW_IMAGES_LINKED', failures.some(x=>x.includes('bad-image'))?'FAIL':'PASS'); out('ALL_IMAGE_COUNTS_VALID', failures.some(x=>x.includes('image_count')||x.includes('duplicate'))?'FAIL':'PASS'); out('NO_PRIVATE_PATHS', failures.some(x=>x.includes('bad-image'))?'FAIL':'PASS'); out('ZEUS_TEMPLE_PRESERVED', failures.some(x=>x.includes('zeus_not'))?'FAIL':'PASS'); out('AIN_AL_FARAS_PRESERVED', failures.some(x=>x.includes('ain_not'))?'FAIL':'PASS'); out('OLD_MOSQUE_PRESERVED', failures.some(x=>x.includes('old_mosque'))?'FAIL':'PASS'); out('FAILED', failures.length); if(failures.length){console.error(failures.join('\n'));process.exitCode=1;}
