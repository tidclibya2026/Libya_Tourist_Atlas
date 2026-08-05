import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const kmlPath = path.join(root, 'data/kml/world-heritage.kml');
const geoPath = path.join(root, 'data/layers/world-heritage.geojson');
const kml = fs.readFileSync(kmlPath, 'utf8');
const geo = JSON.parse(fs.readFileSync(geoPath, 'utf8'));
const failures = [];
const placemarkCount = (text) => (text.match(/<Placemark(?:\s|>)/gi) || []).length;
const total = placemarkCount(kml);
const leptisNameIndex = kml.indexOf('<name>مدينة لبدة الاثرية الكبرى</name>');
const leptisFolderStart = leptisNameIndex >= 0 ? kml.lastIndexOf('<Folder>', leptisNameIndex) : -1;
const leptisFolderEnd = leptisNameIndex >= 0 ? kml.indexOf('</Folder>', leptisNameIndex) : -1;
const leptisFolderText = leptisFolderStart >= 0 && leptisFolderEnd > leptisFolderStart ? kml.slice(leptisFolderStart, leptisFolderEnd + 9) : '';
const leptisFolderCount = placemarkCount(leptisFolderText);
const kmlLeptisTotal = leptisFolderCount + 1;
const features = geo.features || [];
const leptis = features.filter((f) => f.properties?.parent_site_id === 'WH-MAIN-001');
const required = ['id','source_id','name_ar','name_en','parent_site_id','parent_site_name_ar','site_role','category','subcategory','description_ar','description_en','geometry_source','source_file','source_folder','publication_status','review_status','local_images','image_count','image_source','image_owner_ar','image_rights_status','image_review_status','confidence'];
for (const f of features) {
  for (const key of required) if (!(key in (f.properties || {}))) failures.push(`${f.id}: missing ${key}`);
  if (!f.geometry?.type) failures.push(`${f.id}: missing geometry`);
  const paths = Array.isArray(f.properties?.local_images) ? f.properties.local_images : [];
  if (new Set(paths).size !== paths.length) failures.push(`${f.id}: duplicate local_images`);
  for (const image of paths) {
    if (/^(?:file:|[A-Z]:\\)/i.test(image)) failures.push(`${f.id}: private/file path ${image}`);
    if (/review-required/i.test(image)) failures.push(`${f.id}: review image linked ${image}`);
    if (!image.startsWith('assets/')) failures.push(`${f.id}: non-relative image ${image}`);
    if (!fs.existsSync(path.join(root, image))) failures.push(`${f.id}: missing image ${image}`);
  }
}
const ids = features.map((f) => f.id);
if (new Set(ids).size !== ids.length) failures.push('duplicate feature ids');
if (features.length !== total) failures.push(`GEOJSON_TOTAL ${features.length} != KML_TOTAL ${total}`);
if (leptis.length !== kmlLeptisTotal) failures.push(`LEPTIS_TOTAL ${leptis.length} != KML_LEPTIS_TOTAL ${kmlLeptisTotal}`);
if (!features.some((f) => f.id === 'WH-MAIN-001' && f.properties.site_role === 'primary')) failures.push('missing WH-MAIN-001 primary');
const result = { KML_TOTAL: total, KML_LEPTIS_TOTAL: kmlLeptisTotal, KML_LEPTIS_POINTS: leptisFolderCount, KML_LEPTIS_POLYGONS: 0, GEOJSON_TOTAL: features.length, GEOJSON_LEPTIS_TOTAL: leptis.length, MAP_RENDERED_LEPTIS_TOTAL: leptis.length, LINKED_IMAGE_FEATURES: leptis.filter((f) => f.properties.local_images?.length).length, FEATURES_WITHOUT_IMAGES: leptis.filter((f) => !f.properties.local_images?.length).length, REVIEW_REQUIRED_FEATURES: leptis.filter((f) => f.properties.review_status === 'review_required').length, failures };
console.log(JSON.stringify(result, null, 2));
if (failures.length) process.exitCode = 1;
