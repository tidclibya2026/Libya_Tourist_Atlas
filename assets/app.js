'use strict';

const DEBUG_MEDIA = false;

const PLACEHOLDER_IMAGE = resolveAssetPath('assets/images/placeholders/location-placeholder.svg');

const layers = [
  {
    id: 'heritage',
    name: 'مواقع التراث العالمي',
    file: 'data/kml/final/world-heritage.kml',
    icon: '🏛️',
    color: '#7c3aed',
    meta: 'التراث العالمي والصور المرتبطة'
  },
  {
    id: 'akakus',
    name: 'تادرارت أكاكوس والفن الصخري',
    file: 'data/kml/final/akakus.kml',
    icon: '🪨',
    color: '#b45309',
    meta: 'الفن الصخري والمشهد الصحراوي'
  },
{
  id: 'oldTripoli',
  name: 'المدينة القديمة طرابلس',
  file: 'data/kml/final/old-tripoli.kml',
  icon: '🕌',
  color: '#0891b2',
  meta: 'المعالم التاريخية والصور المحلية'
},
  {
    id: 'hotels',
    name: 'الفنادق',
    file: 'data/kml/final/hotels.kml',
    icon: '🏨',
    color: '#dc2626',
    meta: 'منشآت الإيواء السياحي'
  },
  {
    id: 'resorts',
    name: 'القرى والمنتجعات السياحية',
    file: 'data/kml/final/resorts.kml',
    icon: '🏖️',
    color: '#0d9488',
    meta: 'القرى والمنتجعات والشاليهات'
  },
  {
    id: 'investment',
    name: 'المشاريع وفرص الاستثمار',
    file: 'data/kml/final/investment.kml',
    icon: '📈',
    color: '#ca8a04',
    meta: 'مواقع التنمية والفرص الاستثمارية'
  },
  {
    id: 'naturalGithub',
    name: 'أطلس الموارد الطبيعية – GitHub',
    type: 'geojson',
    url: 'https://raw.githubusercontent.com/tidclibya/libyan--map/main/mapatlas.geojson',
    filter: 'natural',
    icon: '🌿',
    color: '#15803d',
    meta: 'ربط مباشر بالمصدر المنشور على GitHub'
  },
  {
    id: 'national',
    name: 'السجل الوطني الموحد',
    file: 'data/kml/final/national-atlas.kml',
    icon: '🇱🇾',
    color: '#1d4ed8',
    meta: '24,454 سجلًا – يحمّل عند الطلب'
  }
];

const layerNamesEn = { heritage: 'World Heritage', akakus: 'Akakus', oldTripoli: 'Old Tripoli', hotels: 'Hotels', resorts: 'Resorts', investment: 'Investment', naturalGithub: 'Natural Resources', national: 'National Atlas' };
for (const cfg of layers) {
  Object.assign(cfg, { nameAr: cfg.name, nameEn: layerNamesEn[cfg.id] || cfg.name, visibleByDefault: cfg.id === 'heritage', cluster: true, popupType: 'gallery' });
}

const map = L.map('map', {
  zoomControl: true,
  minZoom: 4
}).setView([27.2, 17.2], 5);

const baseLayers = {
  'خريطة فاتحة': L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    {
      maxZoom: 19,
      attribution: '© OpenStreetMap © CARTO'
    }
  ),
  'قمر صناعي': L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    {
      maxZoom: 19,
      attribution: 'Tiles © Esri'
    }
  )
};

baseLayers['خريطة فاتحة'].addTo(map);
L.control.layers(baseLayers, null, { position: 'topleft' }).addTo(map);

const state = {};
let loadingRequests = 0;

const list = document.getElementById('layerList');

for (const cfg of layers) {
  const card = document.createElement('div');
  card.className = 'layer-card';

  card.innerHTML = `
    <div class="layer-icon" style="background:${cfg.color}">
      ${cfg.icon}
    </div>
    <div>
      <div class="layer-name">${cfg.name}</div>
      <div class="layer-meta">${cfg.meta}</div>
    </div>
    <label class="switch">
      <input type="checkbox" data-id="${cfg.id}">
      <span></span>
    </label>
  `;

  list.appendChild(card);

  card.querySelector('input').addEventListener('change', event => {
    toggleLayer(cfg, event.target.checked);
  });
}

function markerIcon(cfg) {
  return L.divIcon({
    className: '',
    html: `
      <div style="
        width:30px;
        height:30px;
        border-radius:10px;
        background:${cfg.color};
        color:white;
        display:grid;
        place-items:center;
        border:2px solid white;
        box-shadow:0 3px 9px #0004;
        font-size:16px;
      ">
        ${cfg.icon}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  });
}

function extractPlacemarkProperties(placemark, kmlFileUrl) {
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
  const gallery = photoPaths.length ? `<div class="popup-gallery">${photoPaths.map((path,index)=>`
    <button type="button" class="popup-image-button ${index===0?'popup-image-main':''}" data-image="${escapeAttribute(path)}" aria-label="عرض صورة الموقع">
      <span class="popup-image-loader"></span><img src="${escapeAttribute(path)}" alt="${escapeAttribute(name)} - صورة ${index+1}" loading="lazy" decoding="async" referrerpolicy="no-referrer">
    </button>`).join('')}</div>` : '';
  const details = [properties.category, properties.city, properties.address, properties.phone].filter(Boolean).map(value=>`<div>${escapeHtml(value)}</div>`).join('');
  layer.bindPopup(`<article class="tourism-popup" dir="rtl">${gallery}<div class="popup-body"><h3 class="popup-title">${escapeHtml(name)}</h3>${details}<div class="popup-description">${cleanText || 'بيانات الموقع ضمن طبقة أطلس ليبيا السياحي.'}</div><div class="popup-source">${escapeHtml(cfg.name)} · نسخة عرض مؤسسية</div></div></article>`,{maxWidth:440,minWidth:300,className:'atlas-popup'});
  layer.on('popupopen', event => {
    const container=event.popup.getElement();if(!container)return;
    container.querySelectorAll('.popup-image-button').forEach(button=>{const img=button.querySelector('img'),loader=button.querySelector('.popup-image-loader');
      img?.addEventListener('load',()=>{img.classList.add('is-loaded');loader?.remove()},{once:true});
      img?.addEventListener('error',()=>{if(img.dataset.fallback==='1'){button.remove();return}img.dataset.fallback='1';img.src=PLACEHOLDER_IMAGE},{once:false});
      button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();openAtlasImage(button.dataset.image||'')});
    });
  });
}

function extractPhotoPaths(rawDescription, props = {}) {
  const paths = new Set();

  const candidates = [
    rawDescription,
    props.photo,
    props.photos,
    props.image,
    props.images,
    props.popupinfo,
    props.PopupInfo
  ];

  for (const candidate of candidates) {
    if (!candidate) {
      continue;
    }

    const text = String(candidate?.value || candidate);

    extractJsonPhotoPaths(text, paths);
    extractLoosePathnames(text, paths);
    extractHtmlImages(text, paths);
  }

  return Array.from(paths).map(url => normalizeMediaUrl(url)).filter(Boolean);
}

function extractJsonPhotoPaths(text, paths) {
  const marker = '___json';
  let start = 0;

  while (true) {
    const markerIndex = text.indexOf(marker, start);

    if (markerIndex === -1) {
      break;
    }

    const arrayStart = text.indexOf('[', markerIndex);

    if (arrayStart === -1) {
      break;
    }

    const jsonBlock = readBalancedJsonArray(text, arrayStart);

    if (jsonBlock) {
      try {
        const parsed = JSON.parse(jsonBlock);

        if (Array.isArray(parsed)) {
          for (const photo of parsed) {
            const pathname =
              photo?.pathname ||
              photo?.path ||
              photo?.url ||
              photo?.src;

            if (pathname) {
              paths.add(normalizeKmlPhotoPath(pathname));
            }
          }
        }
      } catch (error) {
        console.warn('تعذر تحليل JSON الصور داخل KML:', error);
      }

      start = arrayStart + jsonBlock.length;
    } else {
      start = arrayStart + 1;
    }
  }
}

function readBalancedJsonArray(text, startIndex) {
  let depth = 0;
  let inString = false;
  let escaped = false;

  for (let index = startIndex; index < text.length; index += 1) {
    const char = text[index];

    if (inString) {
      if (escaped) {
        escaped = false;
        continue;
      }

      if (char === '\\') {
        escaped = true;
        continue;
      }

      if (char === '"') {
        inString = false;
      }

      continue;
    }

    if (char === '"') {
      inString = true;
      continue;
    }

    if (char === '[') {
      depth += 1;
    } else if (char === ']') {
      depth -= 1;

      if (depth === 0) {
        return text.slice(startIndex, index + 1);
      }
    }
  }

  return '';
}

function extractLoosePathnames(text, paths) {
  const pathnameRegex =
    /["']pathname["']\s*:\s*["']([^"']+)["']/gi;

  for (const match of text.matchAll(pathnameRegex)) {
    paths.add(normalizeKmlPhotoPath(match[1]));
  }
}

function extractHtmlImages(text, paths) {
  const imgRegex =
    /<img[^>]+src=["']([^"']+)["']/gi;

  for (const match of text.matchAll(imgRegex)) {
    paths.add(normalizeKmlPhotoPath(match[1]));
  }
}

function resolveAssetPath(assetPath) {
  return new URL(String(assetPath || '').replace(/^\/+/, ''), document.baseURI).href;
}

function normalizeMediaUrl(path, kmlFileUrl = '') {
  return AtlasMediaUtils.normalizeMediaUrl(path, kmlFileUrl);
}

const normalizeKmlPhotoPath = normalizeMediaUrl;

function decodeURIComponentSafe(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function getSiteBasePath() {
  const pathname = window.location.pathname;

  if (pathname.includes('/Libya_Tourist_Atlas/')) {
    return '/Libya_Tourist_Atlas/';
  }

  return '/';
}

function cleanDescriptionText(rawHtml) {
  let text = String(rawHtml || '');

  text = removeJsonPhotoBlocks(text);

  const doc = new DOMParser().parseFromString(
    text,
    'text/html'
  );

  doc.querySelectorAll('img, iframe, script, style').forEach(element => {
    element.remove();
  });

  doc.querySelectorAll('*').forEach(element => {
    for (const attribute of [...element.attributes]) {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.toLowerCase();

      if (
        name.startsWith('on') ||
        value.includes('javascript:')
      ) {
        element.removeAttribute(attribute.name);
      }
    }
  });

  return doc.body.innerHTML.trim();
}

function removeJsonPhotoBlocks(text) {
  let result = text;
  const marker = '___json';
  let guard = 0;

  while (guard < 100) {
    guard += 1;

    const markerIndex = result.indexOf(marker);

    if (markerIndex === -1) {
      break;
    }

    const arrayStart = result.indexOf('[', markerIndex);

    if (arrayStart === -1) {
      result =
        result.slice(0, markerIndex) +
        result.slice(markerIndex + marker.length);

      continue;
    }

    const jsonBlock = readBalancedJsonArray(
      result,
      arrayStart
    );

    if (!jsonBlock) {
      result =
        result.slice(0, markerIndex) +
        result.slice(arrayStart + 1);

      continue;
    }

    const lineBreakIndex = result.lastIndexOf('\n', markerIndex);
    const htmlBreakIndex = result.lastIndexOf('<br', markerIndex);
    const photoIndex = result.lastIndexOf('photo', markerIndex);

    const removeStart = Math.max(
      lineBreakIndex,
      htmlBreakIndex,
      photoIndex,
      markerIndex
    );

    result =
      result.slice(0, removeStart) +
      result.slice(arrayStart + jsonBlock.length);
  }

  return result
    .replace(/photo\s*:\s*/gi, '')
    .replace(/pathname\s*:\s*/gi, '')
    .replace(/<br\s*\/?>\s*<br\s*\/?>/gi, '<br>');
}

function escapeHtml(value) {
  return String(value).replace(
    /[&<>"']/g,
    char =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[char]
  );
}

function escapeAttribute(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function openAtlasImage(source) {
  if (!source) {
    return;
  }

  const viewer = document.createElement('div');
  viewer.className = 'atlas-image-viewer';

  viewer.innerHTML = `
    <button
      type="button"
      class="atlas-image-close"
      aria-label="إغلاق الصورة"
    >
      ×
    </button>

    <img
      src="${escapeAttribute(source)}"
      alt="صورة الموقع السياحي"
      referrerpolicy="no-referrer"
    >
  `;

  viewer.addEventListener('click', event => {
    if (
      event.target === viewer ||
      event.target.classList.contains('atlas-image-close')
    ) {
      viewer.remove();
    }
  });

  document.addEventListener(
    'keydown',
    event => {
      if (event.key === 'Escape') {
        viewer.remove();
      }
    },
    { once: true }
  );

  document.body.appendChild(viewer);
}

function naturalFeature(feature) {
  const props = feature.properties || {};

  const text = (
    `${props.name || ''} ${
      props.description?.value ||
      props.description ||
      ''
    }`
  ).toLowerCase();

  return [
    'بحيرة',
    'وادي',
    'جبل',
    'كهف',
    'شاط',
    'جزيرة',
    'سبخة',
    'غابة',
    'طبيع',
    'قوس صخري',
    'شلال',
    'عين',
    'نبع',
    'رمال',
    'كثبان',
    'واحة',
    'محمية',
    'خليج'
  ].some(keyword => text.includes(keyword));
}

async function toggleLayer(cfg, on) {
  if (!on) {
    if (state[cfg.id]?.group) {
      map.removeLayer(state[cfg.id].group);
      updateStats();
    }

    return;
  }

  if (state[cfg.id]?.group) {
    state[cfg.id].group.addTo(map);
    fit(state[cfg.id].group);
    updateStats();
    return;
  }

  beginLoading();

  try {
    const cluster = L.markerClusterGroup({
      chunkedLoading: true,
      maxClusterRadius: 48
    });

    let count = 0;

    if (cfg.type === 'geojson') {
      const response = await fetch(cfg.url);

      if (!response.ok) {
        throw new Error(`GitHub ${response.status}`);
      }

      const data = await response.json();

      L.geoJSON(data, {
        filter: feature =>
          cfg.filter === 'natural'
            ? naturalFeature(feature)
            : true,

        pointToLayer: (feature, latLng) =>
          L.marker(latLng, {
            icon: markerIcon(cfg)
          }),

        onEachFeature: (feature, leafletLayer) => {
          cleanPopup(leafletLayer, cfg);
          cluster.addLayer(leafletLayer);
          count += 1;
        }
      });
    } else {
      const kmlFileUrl = resolveAssetPath(cfg.file);
      const response = await fetch(kmlFileUrl);
      if (!response.ok) throw new Error(`KML ${response.status}: ${cfg.file}`);
      const kmlText = await response.text();
      const xml = new DOMParser().parseFromString(kmlText, 'application/xml');
      if (xml.querySelector('parsererror')) throw new Error(`Invalid KML XML: ${cfg.file}`);
      const placemarks = [...xml.getElementsByTagNameNS('*', 'Placemark')];
      const parser = omnivore.kml.parse(kmlText, null, L.geoJSON(null, {
        pointToLayer: (feature, latLng) => L.marker(latLng, { icon: markerIcon(cfg) })
      }));
      let index = 0;
      parser.eachLayer(leafletLayer => {
        cleanPopup(leafletLayer, cfg, placemarks[index] || '', kmlFileUrl);
        cluster.addLayer(leafletLayer); index += 1; count += 1;
      });
    }    state[cfg.id] = {
      group: cluster,
      count
    };

    cluster.addTo(map);
    fit(cluster);
    updateStats();
  } catch (error) {
    console.error(error);
    alert(`تعذر تحميل طبقة: ${cfg.name}`);

    const checkbox = document.querySelector(
      `[data-id="${cfg.id}"]`
    );

    if (checkbox) {
      checkbox.checked = false;
    }
  } finally {
    endLoading();
  }
}

function fit(group) {
  try {
    const bounds = group.getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.08), {
        maxZoom: 11
      });
    }
  } catch {
    // تجاهل الطبقات التي لا تملك حدودًا صالحة.
  }
}

function updateStats() {
  let loaded = 0;
  let visible = 0;

  for (const value of Object.values(state)) {
    if (
      value.group &&
      map.hasLayer(value.group)
    ) {
      loaded += 1;
      visible += value.count || 0;
    }
  }

  document.getElementById(
    'loadedCount'
  ).textContent = loaded.toLocaleString('ar');

  document.getElementById(
    'featureCount'
  ).textContent = visible.toLocaleString('ar');
}

function beginLoading() {
  loadingRequests += 1;

  const element = document.getElementById('loading');

  if (element) {
    element.hidden = false;
  }
}

function endLoading() {
  loadingRequests = Math.max(
    0,
    loadingRequests - 1
  );

  const element = document.getElementById('loading');

  if (element) {
    element.hidden = loadingRequests === 0;
  }
}

document.getElementById('clearBtn').onclick = () => {
  document.querySelectorAll('.switch input').forEach(input => {
    input.checked = false;
  });

  Object.values(state).forEach(value => {
    if (value.group) {
      map.removeLayer(value.group);
    }
  });

  updateStats();
};

document.getElementById('searchBtn').onclick = search;

document.getElementById('searchInput').addEventListener(
  'keydown',
  event => {
    if (event.key === 'Enter') {
      search();
    }
  }
);

function search() {
  const query = document
    .getElementById('searchInput')
    .value
    .trim()
    .toLowerCase();

  if (!query) {
    return;
  }

  for (const value of Object.values(state)) {
    if (
      !value.group ||
      !map.hasLayer(value.group)
    ) {
      continue;
    }

    let found = null;

    value.group.eachLayer(layer => {
      if (found) {
        return;
      }

      const props =
        layer.feature?.properties || {};

      const searchable = [
        props.name,
        props.ar_name,
        props.en_name,
        props.description?.value,
        props.description
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      if (searchable.includes(query)) {
        found = layer;
      }
    });

    if (found) {
      if (typeof found.getLatLng === 'function') {
        map.setView(found.getLatLng(), 14);
      } else if (
        typeof found.getBounds === 'function'
      ) {
        map.fitBounds(found.getBounds(), {
          maxZoom: 14
        });
      }

      found.openPopup();
      return;
    }
  }

  alert('لم يُعثر على الموقع داخل الطبقات المحمّلة.');
}

document.getElementById('mobileToggle').onclick = () => {
  document
    .getElementById('sidebar')
    .classList.toggle('open');
};

setTimeout(() => {
  const checkbox = document.querySelector(
    '[data-id="heritage"]'
  );

  if (checkbox) {
    checkbox.checked = true;
    toggleLayer(layers[0], true);
  }
}, 350);





