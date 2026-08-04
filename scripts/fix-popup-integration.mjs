import fs from 'node:fs';
const appFile='assets/app.js',indexFile='index.html';let s=fs.readFileSync(appFile,'utf8');
const replaceOnce=(a,b)=>{if(!s.includes(a))throw new Error(`Missing expected app fragment: ${a.slice(0,80)}`);s=s.replace(a,b)};
replaceOnce("'use strict';","'use strict';\n\nconst DEBUG_MEDIA = false;");
const popupStart=s.indexOf('function cleanPopup('),popupEnd=s.indexOf('function extractPhotoPaths',popupStart);if(popupStart<0||popupEnd<0)throw new Error('popup block not found');
const popup=`function extractPlacemarkProperties(placemark, kmlFileUrl) {
  return AtlasMediaUtils.extractPlacemarkProperties(placemark, kmlFileUrl);
}

function extractPlacemarkImages(placemark, properties, kmlFileUrl) {
  return AtlasMediaUtils.extractPlacemarkImages(placemark, properties, kmlFileUrl);
}

function cleanPopup(layer, cfg, placemark, kmlFileUrl) {
  const parsed = extractPlacemarkProperties(placemark, kmlFileUrl);
  const featureProps = layer.feature?.properties || {};
  const properties = { ...featureProps, ...parsed, _raw: parsed._raw };
  const name = properties.nameAr || properties.nameEn || featureProps.name || 'موقع سياحي';
  const rawDescription = properties.description || '';
  const photoPaths = extractPlacemarkImages(placemark, properties, kmlFileUrl).slice(0, 6);
  const cleanText = cleanDescriptionText(rawDescription);
  if (DEBUG_MEDIA) {
    console.group('[Atlas media debug]');
    console.log({ layerId: cfg.id, placemarkName: name, rawImagesJson: properties.images_json || '', extractedImages: photoPaths, normalizedImages: photoPaths });
    console.groupEnd();
  }
  const gallery = photoPaths.length ? \`<div class="popup-gallery">\${photoPaths.map((path,index)=>\`
    <button type="button" class="popup-image-button \${index===0?'popup-image-main':''}" data-image="\${escapeAttribute(path)}" aria-label="عرض صورة الموقع">
      <span class="popup-image-loader"></span><img src="\${escapeAttribute(path)}" alt="\${escapeAttribute(name)} - صورة \${index+1}" loading="lazy" decoding="async" referrerpolicy="no-referrer">
    </button>\`).join('')}</div>\` : '';
  const details = [properties.category, properties.city, properties.address, properties.phone].filter(Boolean).map(value=>\`<div>\${escapeHtml(value)}</div>\`).join('');
  layer.bindPopup(\`<article class="tourism-popup" dir="rtl">\${gallery}<div class="popup-body"><h3 class="popup-title">\${escapeHtml(name)}</h3>\${details}<div class="popup-description">\${cleanText || 'بيانات الموقع ضمن طبقة أطلس ليبيا السياحي.'}</div><div class="popup-source">\${escapeHtml(cfg.name)} · نسخة عرض مؤسسية</div></div></article>\`,{maxWidth:440,minWidth:300,className:'atlas-popup'});
  layer.on('popupopen', event => {
    const container=event.popup.getElement();if(!container)return;
    container.querySelectorAll('.popup-image-button').forEach(button=>{const img=button.querySelector('img'),loader=button.querySelector('.popup-image-loader');
      img?.addEventListener('load',()=>{img.classList.add('is-loaded');loader?.remove()},{once:true});
      img?.addEventListener('error',()=>{if(img.dataset.fallback==='1'){button.remove();return}img.dataset.fallback='1';img.src=PLACEHOLDER_IMAGE},{once:false});
      button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();openAtlasImage(button.dataset.image||'')});
    });
  });
}

`;
s=s.slice(0,popupStart)+popup+s.slice(popupEnd);
const normalStart=s.indexOf('function normalizeMediaUrl('),normalEnd=s.indexOf('const normalizeKmlPhotoPath',normalStart);if(normalStart<0||normalEnd<0)throw new Error('normalizer block not found');s=s.slice(0,normalStart)+`function normalizeMediaUrl(path, kmlFileUrl = '') {\n  return AtlasMediaUtils.normalizeMediaUrl(path, kmlFileUrl);\n}\n\n`+s.slice(normalEnd);
const toggleStart=s.indexOf('async function toggleLayer');const elseStart=s.indexOf('    } else {',toggleStart);const stateStart=s.indexOf('    state[cfg.id]',elseStart);if(elseStart<0||stateStart<0)throw new Error('KML loader block not found');
const loader=`    } else {
      const kmlFileUrl = resolveAssetPath(cfg.file);
      const response = await fetch(kmlFileUrl);
      if (!response.ok) throw new Error(\`KML \${response.status}: \${cfg.file}\`);
      const kmlText = await response.text();
      const xml = new DOMParser().parseFromString(kmlText, 'application/xml');
      if (xml.querySelector('parsererror')) throw new Error(\`Invalid KML XML: \${cfg.file}\`);
      const placemarks = [...xml.getElementsByTagNameNS('*', 'Placemark')];
      const parser = omnivore.kml.parse(kmlText, null, L.geoJSON(null, {
        pointToLayer: (feature, latLng) => L.marker(latLng, { icon: markerIcon(cfg) })
      }));
      let index = 0;
      parser.eachLayer(leafletLayer => {
        cleanPopup(leafletLayer, cfg, placemarks[index] || '', kmlFileUrl);
        cluster.addLayer(leafletLayer); index += 1; count += 1;
      });
    }`;
s=s.slice(0,elseStart)+loader+s.slice(stateStart);
fs.writeFileSync(appFile,s);
let html=fs.readFileSync(indexFile,'utf8');if(!html.includes('assets/media-utils.js'))html=html.replace('  <script src="assets/app.js"></script>','  <script src="assets/media-utils.js"></script>\n  <script src="assets/app.js"></script>');fs.writeFileSync(indexFile,html);
console.log('Popup/KML integration updated.');

