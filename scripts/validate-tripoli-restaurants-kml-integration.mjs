import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const geoPath = path.join(root, 'data/layers/tripoli-restaurants.geojson');
const app = fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8');
const failures = [];
let data;
try { data = JSON.parse(fs.readFileSync(geoPath, 'utf8')); } catch (error) { failures.push(`invalid-json:${error.message}`); data = { features: [] }; }
const features = Array.isArray(data.features) ? data.features : [];
if (data.type !== 'FeatureCollection' || features.length !== 75) failures.push('invalid-feature-collection');
const ids = new Set();
for (const feature of features) {
  const p = feature.properties || {};
  if (!String(p.name_ar || '').trim()) failures.push(`${p.id}:empty-name`);
  if (!p.id || ids.has(p.id)) failures.push(`${p.id}:duplicate-id`); else ids.add(p.id);
  const c = feature.geometry?.coordinates;
  if (feature.geometry?.type !== 'Point' || !Array.isArray(c) || c.length < 2 || !c.every(Number.isFinite)) failures.push(`${p.id}:invalid-coordinate`);
  else if (c[0] < 12.7 || c[0] > 13.6 || c[1] < 32.5 || c[1] > 33.1) failures.push(`${p.id}:outside-tripoli`);
  if (/<(?:img|br|div|script|style)\b|<!\[CDATA\[/i.test(String(p.description_ar || ''))) failures.push(`${p.id}:raw-html`);
  if (/^(?:[A-Za-z]:|file:)|\\/.test(String(p.source_kml || ''))) failures.push(`${p.id}:private-path`);
  const images = Array.isArray(p.local_images) ? p.local_images : [];
  if (p.image_count !== images.length) failures.push(`${p.id}:image-count`);
  for (const image of images) if (/^(?:[A-Za-z]:|file:|https?:)|\\/.test(image) || !fs.existsSync(path.join(root, image.replace(/^\//, '')))) failures.push(`${p.id}:broken-local-image:${image}`);
}
if (!/id:\s*'tripoliRestaurants'[\s\S]*?type:\s*'geojson'[\s\S]*?url:\s*'data\/layers\/tripoli-restaurants\.geojson'/.test(app)) failures.push('layer-not-registered');
if (!/properties\.subcategory_ar/.test(app) || !/properties\.cuisine_type_ar/.test(app) || !/properties\.district_ar/.test(app) || !/properties\.opening_hours/.test(app)) failures.push('popup-fields-not-clean');
const status = pattern => failures.some(f => pattern.test(f)) ? 'FAIL' : 'PASS';
console.log(`RESTAURANTS_GEOJSON_VALID = ${status(/invalid-json|invalid-feature-collection/)}`);
console.log(`NO_EMPTY_RESTAURANT_NAMES = ${status(/empty-name/)}`);
console.log(`NO_DUPLICATE_RESTAURANT_IDS = ${status(/duplicate-id/)}`);
console.log(`ALL_RESTAURANT_COORDINATES_VALID = ${status(/invalid-coordinate|outside-tripoli/)}`);
console.log(`NO_RAW_KML_HTML = ${status(/raw-html/)}`);
console.log(`NO_PRIVATE_PATHS = ${status(/private-path/)}`);
console.log(`NO_BROKEN_LOCAL_IMAGES = ${status(/broken-local-image/)}`);
console.log(`IMAGE_COUNT_VALID = ${status(/image-count/)}`);
console.log(`RESTAURANTS_LAYER_REGISTERED = ${status(/layer-not-registered/)}`);
console.log(`RESTAURANTS_POPUP_FIELDS_CLEAN = ${status(/popup-fields-not-clean/)}`);
console.log(`FAILED = ${failures.length}`);
if (failures.length) { console.error(failures.slice(0, 100).join('\n')); process.exitCode = 1; }
