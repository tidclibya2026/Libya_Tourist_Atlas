import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=process.cwd(),context={URL,console,globalThis:null,document:{baseURI:'https://tidclibya2026.github.io/Libya_Tourist_Atlas/'}};context.globalThis=context;vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'assets','media-utils.js'),'utf8'),context);const u=context.AtlasMediaUtils;
const double='&quot;[\\&quot;/assets/images/hotels/a b.jpg\\&quot;]&quot;';
assert.equal(u.normalizeMediaUrl('/assets/images/صور/أ.jpg','',context.document.baseURI),'https://tidclibya2026.github.io/Libya_Tourist_Atlas/assets/images/%D8%B5%D9%88%D8%B1/%D8%A3.jpg');
assert.equal(u.normalizeMediaUrl('javascript:alert(1)'),'');assert.equal(u.normalizeMediaUrl('data:text/html,bad'),'');assert(!u.normalizeMediaUrl('assets/images/a.jpg','',context.document.baseURI).includes('data/kml/final/assets'));
const duplicate='<Placemark><name>X</name><description><![CDATA[<img src="assets/images/a.jpg"><a href="assets/images/a.jpg">x</a>]]></description><ExtendedData><Data name="images_json"><value>["assets/images/a.jpg"]</value></Data></ExtendedData></Placemark>';
const dp=u.extractPlacemarkProperties(duplicate,'x.kml'),di=u.extractPlacemarkImages(duplicate,dp,'x.kml',context.document.baseURI);assert.equal(di.length,1);assert.equal(dp.nameAr,'X');
for(const id of ['akakus','old-tripoli','hotels','world-heritage','resorts','investment']){const text=fs.readFileSync(path.join(root,'data','kml','final',`${id}.kml`),'utf8'),ps=[...text.matchAll(/<Placemark\b[\s\S]*?<\/Placemark>/gi)].map(m=>m[0]);let found=0;for(const pm of ps){const props=u.extractPlacemarkProperties(pm,`${id}.kml`),images=u.extractPlacemarkImages(pm,props,`${id}.kml`,context.document.baseURI);if(images.length)found++;if(found>=10)break}assert(found>0,`${id}: no images extracted`);console.log(`${id}: ${found} image-bearing samples parsed`)}
console.log('Popup media tests passed: JSON/HTML extraction, safe URLs, deduplication, GitHub Pages base path, six layers.');
