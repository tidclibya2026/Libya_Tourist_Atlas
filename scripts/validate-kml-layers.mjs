import fs from 'node:fs';
import path from 'node:path';

const root=process.cwd(),dir=path.join(root,'data','kml','final');
const ids=['akakus','old-tripoli','hotels','world-heritage','resorts','investment','national-atlas'];
const errors=[],seen=new Set();let points=0;
const decode=s=>String(s||'').replace(/&amp;/g,'&');
for(const id of ids){const file=path.join(dir,`${id}.kml`);if(!fs.existsSync(file)){errors.push(`missing ${file}`);continue}const text=fs.readFileSync(file,'utf8');
 if(!/<kml\b/i.test(text)||!/<\/kml>/i.test(text))errors.push(`${id}: invalid XML envelope`);
 for(const bad of [/file:\/\//i,/[A-Z]:\\/i,/data\/kml\/assets\/images/i,/\.\.\/assets\/images/i])if(bad.test(text))errors.push(`${id}: forbidden path ${bad}`);
 const ps=[...text.matchAll(/<Placemark\b[\s\S]*?<\/Placemark>/gi)].map(m=>m[0]);points+=ps.length;
 ps.forEach((pm,i)=>{const name=(pm.match(/<name\b[^>]*>([\s\S]*?)<\/name>/i)||[])[1];if(!name||!name.replace(/<!\[CDATA\[|\]\]>/g,'').replace(/<[^>]*>/g,'').trim())errors.push(`${id} #${i+1}: missing name`);const cm=(pm.match(/<coordinates>\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/i)||[]);if(!cm||+cm[1]<-180||+cm[1]>180||+cm[2]<-90||+cm[2]>90)errors.push(`${id} #${i+1}: invalid coordinates`);const aid=(pm.match(/<Data name="atlas_id"><value>([^<]+)/i)||[])[1];if(!aid)errors.push(`${id} #${i+1}: missing atlas_id`);else if(seen.has(aid))errors.push(`${id}: duplicate atlas_id ${aid}`);else seen.add(aid);
  for(const m of decode(pm).matchAll(/\/assets\/images\/([^<&>'",\\]\\s]+)/gi)){let rel=m[1].split(/[?#]/)[0];try{rel=decodeURIComponent(rel)}catch{}const p=path.join(root,'assets','images',...rel.split('/'));if(!fs.existsSync(p))errors.push(`${id} #${i+1}: missing image /assets/images/${rel}`)}})}
console.log(`Validated ${ids.length} layers and ${points} placemarks.`);if(errors.length){console.error(errors.slice(0,200).join('\n'));console.error(`Total errors: ${errors.length}`);process.exit(1)}console.log('KML validation passed.');


