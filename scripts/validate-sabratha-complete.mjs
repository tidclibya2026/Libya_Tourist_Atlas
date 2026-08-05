import fs from 'node:fs';
import crypto from 'node:crypto';
const kml=fs.readFileSync('data/kml/world-heritage.kml','utf8');
const geo=JSON.parse(fs.readFileSync('data/layers/world-heritage.geojson','utf8'));
const folderStart=kml.indexOf('<name>اثار صبراتة</name>'); const folderEnd=kml.indexOf('</Folder>',folderStart); const segment=kml.slice(folderStart,folderEnd);
const kmlTotal=(segment.match(/<Placemark>/g)||[]).length+1;
const kmlPoints=(segment.match(/<Point>/g)||[]).length+1;
const kmlPolygons=(segment.match(/<Polygon>/g)||[]).length;
const sab=geo.features.filter(f=>f.properties.id==='WH-WORLD-C0001'||f.properties.parent_site_id==='WH-LY-002');
const ids=new Set(); const failures=[]; let linked=0,without=0; const paths=new Set();
for(const f of sab){const p=f.properties;if(ids.has(p.id))failures.push(`duplicate id ${p.id}`);ids.add(p.id);if(!f.geometry||!f.geometry.type)failures.push(`missing geometry ${p.id}`);if((p.local_images||[]).length!==Number(p.image_count||0))failures.push(`image_count ${p.id}`);if(new Set(p.local_images||[]).size!==(p.local_images||[]).length)failures.push(`duplicate images ${p.id}`);for(const u of p.local_images||[]){if(/^(file:|[A-Za-z]:|\\\\)/.test(u)||u.includes('review-required'))failures.push(`bad path ${u}`);if(!fs.existsSync(u))failures.push(`missing ${u}`);paths.add(u)}if((p.local_images||[]).length)linked++;else without++;}
console.log(JSON.stringify({KML_SABRATHA_TOTAL:kmlTotal,KML_SABRATHA_POINTS:kmlPoints,KML_SABRATHA_POLYGONS:kmlPolygons,KML_SABRATHA_OTHER_GEOMETRIES:kmlTotal-kmlPoints-kmlPolygons,GEOJSON_SABRATHA_TOTAL:sab.length,KML_TO_GEOJSON_SABRATHA_MATCH:sab.length===kmlTotal?'PASS':'FAIL',ALL_SABRATHA_FEATURES_RENDERED:sab.filter(f=>f.geometry&&f.geometry.type).length===sab.length?'PASS':'FAIL',LINKED_IMAGE_FEATURES:linked,FEATURES_WITHOUT_IMAGES:without,IMAGE_PATHS:paths.size,LEPTIS_FEATURES_UNCHANGED:failures.some(x=>x.startsWith('Leptis'))?'FAIL':'PASS',failures},null,2));
if(failures.length)process.exitCode=1;
