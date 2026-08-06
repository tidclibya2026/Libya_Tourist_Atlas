import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const geoPath = path.join(root, 'data/layers/hotels.geojson');
const app = fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8');
const failures = [];
let data;
try { data = JSON.parse(fs.readFileSync(geoPath, 'utf8')); } catch (error) { failures.push(`invalid-json:${error.message}`); data = {features: []}; }
const features = Array.isArray(data.features) ? data.features : [];
if (data.type !== 'FeatureCollection' || features.length !== 572) failures.push('invalid-feature-collection');
const ids = new Set();
for (const feature of features) {
  const p = feature.properties || {};
  if (!String(p.name_ar || '').trim()) failures.push(`${p.id}:empty-name`);
  if (!p.id || ids.has(p.id)) failures.push(`${p.id}:duplicate-id`); else ids.add(p.id);
  const c = feature.geometry?.coordinates;
  if (feature.geometry?.type !== 'Point' || !Array.isArray(c) || c.length < 2 || !c.every(Number.isFinite)) failures.push(`${p.id}:invalid-coordinate`);
  else if (c[0] < 9 || c[0] > 26 || c[1] < 19 || c[1] > 34) failures.push(`${p.id}:outside-libya`);
  if (/<(?:img|br|div|script|style)\b|<!\[CDATA\[/i.test(String(p.description_ar || ''))) failures.push(`${p.id}:raw-html`);
  if (/^(?:[A-Za-z]:|file:)|\\/.test(String(p.source_kml || ''))) failures.push(`${p.id}:private-path`);
  const images = Array.isArray(p.local_images) ? p.local_images : [];
  if (p.image_count !== images.length) failures.push(`${p.id}:image-count`);
  for (const image of images) if (/^(?:[A-Za-z]:|file:|https?:)|\\/.test(image) || !fs.existsSync(path.join(root, image.replace(/^\//, '')))) failures.push(`${p.id}:broken-local-image:${image}`);
}
if (!/id:\s*'hotels'[\s\S]*?type:\s*'geojson'[\s\S]*?url:\s*'data\/layers\/hotels\.geojson'/.test(app)) failures.push('layer-not-registered');
if (!/properties\.subcategory_ar/.test(app) || !/properties\.stars/.test(app) || !/properties\.rooms/.test(app) || !/properties\.beds/.test(app)) failures.push('popup-fields-not-clean');
const status = pattern => failures.some(f => pattern.test(f)) ? 'FAIL' : 'PASS';
console.log(`HOTELS_GEOJSON_VALID = ${status(/invalid-json|invalid-feature-collection/)}`);
console.log(`NO_EMPTY_HOTEL_NAMES = ${status(/empty-name/)}`);
console.log(`NO_DUPLICATE_HOTEL_IDS = ${status(/duplicate-id/)}`);
console.log(`ALL_HOTEL_COORDINATES_VALID = ${status(/invalid-coordinate/)}`);
console.log(`ALL_HOTELS_INSIDE_LIBYA_BOUNDS = ${status(/outside-libya/)}`);
console.log(`NO_RAW_KML_HTML_IN_POPUPS = ${status(/raw-html/)}`);
console.log(`NO_PRIVATE_PATHS = ${status(/private-path/)}`);
console.log(`NO_BROKEN_LOCAL_IMAGES = ${status(/broken-local-image/)}`);
console.log(`IMAGE_COUNT_VALID = ${status(/image-count/)}`);
console.log(`HOTELS_LAYER_REGISTERED = ${status(/layer-not-registered/)}`);
console.log(`HOTELS_POPUP_FIELDS_CLEAN = ${status(/popup-fields-not-clean/)}`);
console.log(`FAILED = ${failures.length}`);
if (failures.length) { console.error(failures.slice(0, 100).join('\n')); process.exitCode = 1; }
