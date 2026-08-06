import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const geo = JSON.parse(fs.readFileSync(path.join(root, 'data/layers/world-heritage.geojson'), 'utf8'));
const byId = new Map(geo.features.map(feature => [feature.properties?.id, feature.properties]));
const failures = [];
const expected = new Map([
  ['WH-LY-003-C0001', ['archaeological-theatre', 2]],
  ['WH-LY-003-C0016', ['fountain-of-apollo', 1]],
  ['WH-LY-003-C0022', ['greek-agora', 5]],
  ['WH-LY-003-C0023', ['byzantine-basilica', 5]],
  ['WH-LY-003-C0021', ['temple-of-zeus', 1]],
  ['WH-LY-005-C0004', ['ain-al-faras', 1]],
]);

for (const [id, [slug, count]] of expected) {
  const p = byId.get(id);
  const images = p?.local_images || [];
  if (!p) failures.push(`${id}:missing`);
  if (images.length !== count || p?.image_count !== count) failures.push(`${id}:expected-${count}-images`);
  if (p?.image_match_type !== 'exact_feature' || !String(p?.image_review_status).startsWith('confirmed')) failures.push(`${id}:not-confirmed-exact`);
  for (const image of images) {
    if (!image.includes(slug) || image.includes('review-required') || image.includes('\\') || !fs.existsSync(path.join(root, image))) failures.push(`${id}:bad-image:${image}`);
  }
}

const newIds = [...expected.keys()].slice(0, 4);
const newImageCount = newIds.reduce((sum, id) => sum + (byId.get(id)?.local_images?.length || 0), 0);
if (newImageCount !== 13) failures.push(`confirmed-new-image-count:${newImageCount}`);

const ghadames = geo.features.filter(feature => feature.properties?.parent_site_id === 'WH-LY-005');
for (const feature of ghadames) {
  const p = feature.properties;
  if (p.id === 'WH-LY-005-C0004') continue;
  if ((p.local_images || []).length || p.image_count !== 0 || p.image_match_type !== 'placeholder') failures.push(`${p.id}:ghadames-not-placeholder`);
}

for (const site of ['cyrene', 'ghadames']) {
  const csv = fs.readFileSync(path.join(root, `docs/media-linkage/${site}-visual-image-classification.csv`), 'utf8');
  if (csv.includes('pending_review')) failures.push(`${site}:classification-not-final`);
}

const hasFailure = prefix => failures.some(failure => failure.includes(prefix));
console.log(`CYRENE_CONFIRMED_NEW_IMAGES = ${newImageCount}`);
console.log(`CYRENE_FOUR_FEATURE_LINKS = ${newIds.every(id => !hasFailure(id)) ? 'PASS' : 'FAIL'}`);
console.log(`ZEUS_TEMPLE_PRESERVED = ${!hasFailure('WH-LY-003-C0021') ? 'PASS' : 'FAIL'}`);
console.log(`AIN_AL_FARAS_PRESERVED = ${!hasFailure('WH-LY-005-C0004') ? 'PASS' : 'FAIL'}`);
console.log(`GHADAMES_UNCONFIRMED_PLACEHOLDERS = ${!failures.some(failure => failure.includes('ghadames-not-placeholder')) ? 'PASS' : 'FAIL'}`);
console.log(`FINAL_CLASSIFICATION_FILES = ${!failures.some(failure => failure.includes('classification-not-final')) ? 'PASS' : 'FAIL'}`);
console.log(`FAILED = ${failures.length}`);
if (failures.length) {
  console.error(failures.join('\n'));
  process.exitCode = 1;
}
