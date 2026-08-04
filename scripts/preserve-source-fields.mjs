import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd(),base=path.join(root,'data','kml');
const map={akakus:'developed/akakus-developed.kml','old-tripoli':'developed/old-tripoli-developed.kml',hotels:'developed/hotels-developed.kml','world-heritage':'world-heritage-local-images.kml',resorts:'resorts.kml',investment:'investment.kml','national-atlas':'national-atlas.kml'};
const pms=s=>[...s.matchAll(/<Placemark\b[\s\S]*?<\/Placemark>/gi)].map(m=>m[0]);
const strip=s=>String(s||'').replace(/<!\[CDATA\[|\]\]>/g,'').replace(/<[^>]*>/g,' ').replace(/&amp;/g,'&').replace(/\s+/g,' ').trim();
const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
for(const [id,source] of Object.entries(map)){
 const srcText=fs.readFileSync(path.join(base,source),'utf8'),file=path.join(base,'final',`${id}.kml`),finalText=fs.readFileSync(file,'utf8'),src=pms(srcText),fin=pms(finalText);if(src.length!==fin.length)throw new Error(`${id}: count mismatch`);
 let n=0;const merged=finalText.replace(/<Placemark\b[\s\S]*?<\/Placemark>/gi,()=>{const original=src[n],generated=fin[n++],data=[...generated.matchAll(/<Data name="(?:atlas_id|layer_id|layer_name_ar|layer_name_en|name_ar|latitude|longitude|images_json|image_count|source_file|source_placemark_index|data_quality_status)">[\s\S]*?<\/Data>/gi)].map(m=>m[0]).join('');let pm=original;
  const existingName=strip((pm.match(/<name\b[^>]*>([\s\S]*?)<\/name>/i)||[,''])[1]);if(!existingName){const field=name=>strip((pm.match(new RegExp(`<(?:SimpleData|Data)\\b[^>]*name=["']${name}["'][^>]*>(?:<value>)?([\\s\\S]*?)(?:<\\/value>)?<\\/(?:SimpleData|Data)>`,'i'))||[,''])[1]);const fallback=field('name_ar')||field('name_en')||field('name')||[field('fclass'),field('osm_id')].filter(Boolean).join(' ')||`${id} ${n}`;pm=pm.replace(/(<Placemark\b[^>]*>)/i,`$1<name>${esc(fallback)}</name>`)}
  return /<ExtendedData>/i.test(pm)?pm.replace(/<\/ExtendedData>/i,`${data}</ExtendedData>`):pm.replace(/<\/Placemark>/i,`<ExtendedData>${data}</ExtendedData></Placemark>`)});fs.writeFileSync(file,merged);console.log(`${id}: ${n}`)}


