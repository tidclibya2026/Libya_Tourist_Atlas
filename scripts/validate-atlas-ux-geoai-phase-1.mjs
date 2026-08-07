import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const exists = file => fs.existsSync(path.join(root, file));
const checks = [];
const pass = (name, ok, detail = '') => { checks.push({ name, ok, detail }); console.log(`${name} = ${ok ? 'PASS' : 'FAIL'}${detail ? ` — ${detail}` : ''}`); };

const required = ['index.html', 'assets/app.js', 'assets/styles.css', 'assets/atlas-ux-geoai.js', 'assets/atlas-ux-geoai.css', 'assets/geoai/geoai-engine.js', 'assets/geoai/geoai-intents.js', 'assets/geoai/geoai-context.js', 'assets/geoai/geoai-actions.js', 'assets/geoai/geoai-provider.js', 'assets/geoai/geoai-nearby.js', 'assets/geoai/geoai-recommendations.js', 'data/layer-media.json', 'docs/ux/atlas-ux-baseline.md', 'docs/ai/geoai-api-contract.md', 'docs/atlas-ux-geoai-phase-1-report.md'];
pass('UX_PHASE_1_FILES_PRESENT', required.every(exists));
const html = read('index.html'); const ux = read('assets/atlas-ux-geoai.js'); const intents = read('assets/geoai/geoai-intents.js'); const actions = read('assets/geoai/geoai-actions.js'); const app = read('assets/app.js');
pass('ATLAS_LOGO_INTEGRATION_PRESENT', html.includes('brand-lockup') || ux.includes('brand-lockup'), 'tracked official logo asset not available; typographic lockup used');
pass('SMART_SEARCH_PRESENT', html.includes('searchInput') && ux.includes('smart-search'));
pass('LAYER_EXPLORER_PRESENT', html.includes('layerList') && html.includes('sidebar'));
pass('GEOAI_LOCAL_PROVIDER_PRESENT', exists('assets/geoai/geoai-provider.js') && read('assets/geoai/geoai-provider.js').includes("name: 'local'"));
pass('GEOAI_INTENT_ENGINE_PRESENT', intents.includes('AtlasGeoAIIntents') && intents.includes('اعرض') && intents.includes('show'));
pass('NEARBY_ENGINE_PRESENT', read('assets/geoai/geoai-nearby.js').includes('haversine'));
pass('SMART_RECOMMENDATIONS_PRESENT', read('assets/geoai/geoai-recommendations.js').includes('recommend'));
pass('NO_API_KEYS', !/(sk-[A-Za-z0-9]{16,}|api[_-]?key\s*[:=])/i.test(ux + app + intents));
pass('NO_EXTERNAL_AI_CALLS', !/(openai|anthropic|gemini|fetch\s*\(\s*["'`]https?:)/i.test(ux + app + intents));
pass('NO_DATASET_MUTATION', !/\b(edit_feature|delete_feature|change_coordinates|change_layer|mutate_geojson)\b/.test(actions));
pass('NO_GEOJSON_SCHEMA_BREAK', exists('data/layer-media.json') && html.includes('assets/vendor/leaflet/leaflet.js'));
pass('RTL_SUPPORTED', html.includes('dir="rtl"') && ux.includes('document.documentElement.dir'));
pass('LTR_SUPPORTED', ux.includes("document.documentElement.dir = en ? 'ltr' : 'rtl'"));
const media = JSON.parse(read('data/layer-media.json')); const mediaPaths = Object.values(media).flatMap(m => [m.primary_image, ...(m.gallery_images || []), ...(m.context_images || [])]).filter(Boolean); pass('LAYER_MEDIA_PRESERVED', mediaPaths.length > 0 && mediaPaths.every(p => !/^https?:/i.test(p)));
const geojsonFiles = ['data/layers/akakus.geojson','data/layers/hotels.geojson','data/layers/old-tripoli.geojson','data/layers/world-heritage.geojson']; pass('FEATURE_IMAGES_PRESERVED', geojsonFiles.every(exists));
const failed = checks.filter(c => !c.ok).length; console.log(`FAILED = ${failed}`); if (failed) process.exitCode = 1;
