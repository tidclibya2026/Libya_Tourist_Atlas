import fs from 'node:fs';
const file='assets/app.js';let s=fs.readFileSync(file,'utf8');
const replacements=[
 ["data/kml/world-heritage.kml","data/kml/final/world-heritage.kml"],
 ["data/kml/developed/akakus-developed.kml","data/kml/final/akakus.kml"],
 ["data/kml/developed/old-tripoli-developed.kml","data/kml/final/old-tripoli.kml"],
 ["data/kml/developed/hotels-developed.kml","data/kml/final/hotels.kml"],
 ["data/kml/resorts.kml","data/kml/final/resorts.kml"],
 ["data/kml/investment.kml","data/kml/final/investment.kml"],
 ["data/kml/national-atlas.kml","data/kml/final/national-atlas.kml"],
 ["          cfg.file,","          resolveAssetPath(cfg.file),"]
];
for(const [a,b] of replacements){if(!s.includes(a))throw new Error(`Expected text missing: ${a}`);s=s.replace(a,b)}
const old=`function normalizeKmlPhotoPath(path) {
  if (!path) {
    return '';
  }

  let normalized = String(path)
    .trim()
    .replace(/\\\\/g, '/')
    .replace(/^file:\\/+/, '')
    .replace(/^\\.?\\//, '');

  if (
    normalized.startsWith('http://') ||
    normalized.startsWith('https://') ||
    normalized.startsWith('data:image/')
  ) {
    return normalized;
  }

  normalized = normalized
    .split('/')
    .filter(Boolean)
    .map(segment => encodeURIComponent(decodeURIComponentSafe(segment)))
    .join('/');

  return \`\${getSiteBasePath()}\${normalized}\`;
}`;
const next=`function resolveAssetPath(assetPath) {
  return new URL(String(assetPath || '').replace(/^\\/+/, ''), document.baseURI).href;
}

function normalizeMediaUrl(path, kmlFilePath = '') {
  if (!path) return '';
  let normalized = String(path)
    .replace(/&amp;/gi, '&')
    .replace(/\\\\u0026/gi, '&')
    .replace(/[\\u200B-\\u200F\\u202A-\\u202E\\u2060\\uFEFF]/g, '')
    .trim().replace(/\\\\/g, '/').replace(/^file:\\/{0,3}/i, '');
  if (/^(?:javascript|data:text\\/html):/i.test(normalized)) return '';
  if (/^https?:\\/\\//i.test(normalized) || /^data:image\\//i.test(normalized)) return normalized;
  const assetsIndex = normalized.toLowerCase().indexOf('assets/images/');
  normalized = assetsIndex >= 0 ? normalized.slice(assetsIndex) : normalized.replace(/^\\.?\\//, '');
  normalized = normalized.split('/').filter(Boolean)
    .map(segment => encodeURIComponent(decodeURIComponentSafe(segment))).join('/');
  return resolveAssetPath(normalized);
}

const normalizeKmlPhotoPath = normalizeMediaUrl;`;
const start=s.indexOf('function normalizeKmlPhotoPath(path) {'), end=s.indexOf('function decodeURIComponentSafe',start);
if(start<0||end<0)throw new Error('normalizeKmlPhotoPath block changed unexpectedly');s=s.slice(0,start)+next+'\n\n'+s.slice(end);
s=s.replace("  return Array.from(paths).filter(Boolean);","  return Array.from(paths).map(url => normalizeMediaUrl(url)).filter(Boolean);");
s=s.replace("const layers = [","const PLACEHOLDER_IMAGE = resolveAssetPath('assets/images/placeholders/location-placeholder.svg');\n\nconst layers = [");
s=s.replace("                    const button=this.closest('.popup-image-button');\n                    if(button){button.remove();}","                    this.onerror=null;\n                    this.src=PLACEHOLDER_IMAGE;");
fs.writeFileSync(file,s);console.log('assets/app.js updated safely');


