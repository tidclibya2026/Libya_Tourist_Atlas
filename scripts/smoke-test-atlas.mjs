import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
const root=process.cwd(),errors=[];
const html=fs.readFileSync(path.join(root,'index.html'),'utf8'),app=fs.readFileSync(path.join(root,'assets','app.js'),'utf8');
if(!/<script[^>]+src=["']assets\/app\.js["']/i.test(html))errors.push('index.html does not load assets/app.js');
for(const id of ['akakus','old-tripoli','hotels','world-heritage','resorts','investment','national-atlas']){const rel=`data/kml/final/${id}.kml`;if(!app.includes(rel))errors.push(`app.js does not reference ${rel}`);if(!fs.existsSync(path.join(root,...rel.split('/'))))errors.push(`404: ${rel}`)}
if(/data\/kml\/(?:developed|localized)\//i.test(app))errors.push('app.js still uses developed/localized KML');
if(!app.includes('normalizeMediaUrl')||!app.includes('resolveAssetPath'))errors.push('media/path helpers missing');
try{new vm.Script(app,{filename:'assets/app.js'})}catch(e){errors.push(`JavaScript syntax: ${e.message}`)}
if(!fs.existsSync(path.join(root,'assets','images','placeholders','location-placeholder.svg')))errors.push('placeholder missing');
if(errors.length){console.error(errors.join('\n'));process.exit(1)}console.log('Atlas static smoke test passed (HTML, JS syntax, final KML references, local placeholder).');
