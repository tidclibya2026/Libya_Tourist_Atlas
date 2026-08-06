import fs from 'node:fs';

const geoPath = 'data/layers/tourism-investment-projects.geojson';
const appPath = 'assets/app.js';
let failed = 0;
const check = (name, ok) => { console.log(`${name} = ${ok ? 'PASS' : 'FAIL'}`); if (!ok) failed++; };
const data = JSON.parse(fs.readFileSync(geoPath, 'utf8'));
const app = fs.readFileSync(appPath, 'utf8');
const features = data.features || [];
const ids = features.map(f => f.properties?.id);
const names = features.map(f => String(f.properties?.name_ar || '').trim());
const types = features.map(f => f.geometry?.type);
let valid = true, inside = true, closed = true;
const visit = geometry => {
  if (!geometry) { valid = false; return; }
  if (geometry.type === 'Point') {
    const [x,y] = geometry.coordinates || [];
    if (!Number.isFinite(x) || !Number.isFinite(y)) valid = false;
    if (!(x >= 9 && x <= 26 && y >= 19 && y <= 34)) inside = false;
  } else if (geometry.type === 'Polygon' || geometry.type === 'MultiPolygon') {
    const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
    for (const polygon of polygons) for (const ring of polygon) {
      if (!Array.isArray(ring) || ring.length < 4) valid = false;
      if (JSON.stringify(ring[0]) !== JSON.stringify(ring.at(-1))) closed = false;
      for (const [x,y] of ring) {
        if (!Number.isFinite(x) || !Number.isFinite(y)) valid = false;
        if (!(x >= 9 && x <= 26 && y >= 19 && y <= 34)) inside = false;
      }
    }
  } else if (geometry.type === 'GeometryCollection') {
    if (!geometry.geometries?.length) valid = false;
    geometry.geometries?.forEach(visit);
  } else valid = false;
};
features.forEach(f => visit(f.geometry));
const raw = JSON.stringify(data);
const localImages = features.flatMap(f => f.properties?.local_images || []);
const broken = localImages.filter(p => !fs.existsSync(p));

check('INVESTMENT_GEOJSON_VALID', data.type === 'FeatureCollection');
check('INVESTMENT_FEATURE_COUNT_VALID', features.length === data.metadata.feature_count && features.length > 0);
check('POINT_COUNT_VALID', types.filter(x => x === 'Point').length === data.metadata.point_count);
check('POLYGON_COUNT_VALID', types.filter(x => x === 'Polygon' || x === 'MultiPolygon').length === data.metadata.polygon_count);
check('MULTIGEOMETRY_COUNT_VALID', Number.isInteger(data.metadata.multigeometry_count));
check('NO_EMPTY_INVESTMENT_NAMES', names.every(Boolean));
check('NO_DUPLICATE_INVESTMENT_IDS', ids.length === new Set(ids).size && ids.every(Boolean));
check('ALL_INVESTMENT_GEOMETRIES_VALID', valid);
check('ALL_INVESTMENTS_INSIDE_LIBYA_BOUNDS', inside);
check('ALL_POLYGON_RINGS_CLOSED', closed);
check('NO_RAW_KML_HTML', !/<(?:img|table|html|body|br)\b|<!\[CDATA\[/i.test(raw));
check('NO_INVALID_XML_CONTROL_CHARACTERS', !/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(raw));
check('NO_PRIVATE_PATHS', !/[A-Z]:\\Users\\|file:\/\//i.test(raw));
check('NO_BROKEN_LOCAL_IMAGES', broken.length === 0);
check('IMAGE_COUNT_VALID', features.every(f => f.properties.image_count === (f.properties.local_images || []).length));
check('INVESTMENT_LAYER_REGISTERED', /id:\s*['"]investment['"][\s\S]{0,250}type:\s*['"]geojson['"][\s\S]{0,250}tourism-investment-projects\.geojson/.test(app));
check('INVESTMENT_POINTS_CLUSTERED', /const pointCluster = L\.markerClusterGroup/.test(app) && /isPoint \? pointCluster : shapeGroup/.test(app));
check('INVESTMENT_POLYGONS_RENDERED', /const shapeGroup = L\.featureGroup/.test(app));
check('INVESTMENT_POPUP_FIELDS_CLEAN', app.includes('الجاهزية الاستثمارية الأولية') && app.includes('لا يمثل اعتمادًا قانونيًا'));
check('NO_EAGER_REMOTE_IMAGE_LOADING', features.every(f => !(f.properties.local_images || []).some(x => /^https?:/i.test(x))));
console.log(`FAILED = ${failed}`);
process.exitCode = failed ? 1 : 0;
