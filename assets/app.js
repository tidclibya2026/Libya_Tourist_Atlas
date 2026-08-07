'use strict';

const DEBUG_MEDIA = false;

const PLACEHOLDER_IMAGE = resolveAssetPath('assets/images/placeholders/location-placeholder.svg');


const layers = [
  {
    id: 'heritage',
    name: 'مواقع التراث العالمي',
    type: 'geojson',
    url: 'data/layers/world-heritage.geojson',
    hierarchical: true,
    icon: '🏛️',
    color: '#7c3aed',
    meta: '303 عناصر: 5 مواقع رئيسية، 235 معتمدة، 63 قيد المراجعة'
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
    name: 'الفنادق والإيواء',
    type: 'geojson',
    url: 'data/layers/hotels.geojson',
    icon: '🏨',
    color: '#dc2626',
    meta: 'منشآت الإيواء السياحي'
  },
  {
    id: 'tripoliRestaurants',
    name: 'مطاعم طرابلس',
    type: 'geojson',
    url: 'data/layers/tripoli-restaurants.geojson',
    icon: '🍽️',
    color: '#ea580c',
    meta: 'مطاعم ومنشآت طعام في طرابلس'
  },
  {
    id: 'tripoliCafes',
    name: 'مقاهي طرابلس',
    type: 'geojson',
    url: 'data/layers/tripoli-cafes.geojson',
    icon: '☕',
    color: '#92400e',
    meta: 'مقاهٍ ومنشآت مشروبات في طرابلس'
  },
  {
    id: 'resorts',
    name: 'القرى والمنتجعات السياحية',
    type: 'geojson',
    url: 'data/layers/tourist-villages-resorts.geojson',
    icon: '🏖️',
    color: '#0d9488',
    meta: 'القرى والمنتجعات والشاليهات'
  },
  {
    id: 'investment',
    name: 'المشاريع وفرص الاستثمار',
    type: 'geojson',
    url: 'data/layers/tourism-investment-projects.geojson',
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

const layerNamesEn = { heritage: 'World Heritage', akakus: 'Akakus', oldTripoli: 'Old Tripoli', hotels: 'Hotels', tripoliRestaurants: 'Tripoli Restaurants', tripoliCafes: 'Tripoli Cafes', resorts: 'Resorts', investment: 'Investment', naturalGithub: 'Natural Resources', national: 'National Atlas' };
const INTERNAL_ADMIN_MODE = new URLSearchParams(window.location.search).get('mode') === 'internal';
for (const cfg of layers) {
  Object.assign(cfg, { nameAr: cfg.name, nameEn: layerNamesEn[cfg.id] || cfg.name, visibleByDefault: cfg.id === 'heritage', cluster: true, popupType: 'gallery' });
}

const map = L.map('map', {
  zoomControl: true,
  minZoom: 4,
  maxZoom: 19
}).setView([27.2, 17.2], 5);

const baseLayers = window.__ATLAS_OFFLINE__ ? {} : {
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

if (baseLayers['خريطة فاتحة']) baseLayers['خريطة فاتحة'].addTo(map);
L.control.layers(baseLayers, null, { position: 'topleft' }).addTo(map);

const state = {};
window.__atlasTest = { state, layers, map };
let loadingRequests = 0;

const hierarchyStyle =
  document.createElement('style');

hierarchyStyle.textContent = `
  .heritage-hierarchy {
    margin:
      -4px 12px 14px 12px;
    padding:
      8px 12px 10px;
    border-right:
      3px solid #7c3aed;
    border-radius:
      0 0 12px 12px;
    background:
      rgba(124, 58, 237, 0.06);
  }

  .heritage-site-row {
    display:
      grid;
    grid-template-columns:
      20px 1fr auto;
    align-items:
      center;
    gap:
      8px;
    min-height:
      34px;
    cursor:
      pointer;
    border-bottom:
      1px solid rgba(124, 58, 237, 0.1);
  }

  .heritage-site-row:last-child {
    border-bottom:
      0;
  }

  .heritage-site-row input {
    width:
      16px;
    height:
      16px;
    accent-color:
      #7c3aed;
  }

  .heritage-site-name {
    font-size:
      13px;
    font-weight:
      600;
    color:
      #312e81;
  }

  .heritage-site-count {
    min-width:
      27px;
    padding:
      2px 7px;
    border-radius:
      999px;
    text-align:
      center;
    font-size:
      11px;
    font-weight:
      700;
    color:
      #6d28d9;
    background:
      #ede9fe;
  }

  .heritage-site-row:has(
    input:disabled
  ) {
    opacity:
      0.48;
    cursor:
      default;
  }
`;

document.head.appendChild(
  hierarchyStyle
);

const list = document.getElementById('layerList');

for (const cfg of layers) {
  const card = document.createElement('div');
  card.className = 'layer-card';
  card.setAttribute('role', 'listitem');

  card.innerHTML = `
    <div class="layer-icon" style="background:${cfg.color}">
      ${cfg.icon}
    </div>
    <div>
      <div class="layer-name">${cfg.name}</div>
      <div class="layer-meta">${cfg.meta}</div>
      <span class="layer-count-badge" data-layer-count="${cfg.id}">—</span>
    </div>
    <label class="switch">
      <input type="checkbox" data-id="${cfg.id}">
      <span></span>
    </label>
  `;

  list.appendChild(card);

  if (cfg.id === 'heritage') {
    const hierarchy = document.createElement('div');
    hierarchy.id = 'heritageHierarchy';
    hierarchy.className = 'heritage-hierarchy';
    hierarchy.hidden = true;
    hierarchy.innerHTML = `
      <div class="heritage-hierarchy-loading">
        تُبنى قائمة المواقع بعد تحميل الطبقة.
      </div>
    `;
    list.appendChild(hierarchy);
  }

  card.querySelector('input').addEventListener('change', event => {
    toggleLayer(cfg, event.target.checked);
  });
}

function investmentColor(feature, fallback) {
  if (!feature || feature.properties?.category !== 'المشاريع وفرص الاستثمار السياحي') return fallback;
  const p = feature.properties;
  if (p.data_review_status === 'review_required') return '#64748b';
  if (p.project_status_code === 'stalled') return '#b91c1c';
  if (p.project_status_code === 'under_construction') return '#d97706';
  if (p.project_status_code === 'operational') return '#15803d';
  if (p.investment_type_code === 'land_for_tourism_investment') return '#8b5cf6';
  if (p.investment_type_code === 'tourism_development_zone') return '#0369a1';
  if (p.investment_type_code === 'investment_opportunity') return '#ca8a04';
  return fallback;
}

function markerIcon(cfg, feature = null) {
  const color = investmentColor(feature, cfg.color);
  return L.divIcon({
    className: '',
    html: `
      <div style="
        width:30px;
        height:30px;
        border-radius:10px;
        background:${color};
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

function cleanGeoJsonDescription(value) {
  let text = String(value || '');

  text = text
    .replace(/FID:\s*\d+/gi, '')
    .replace(/en_name:\s*[^،\n]+/gi, '')
    .replace(/popupinfo:\s*\{[\s\S]*$/gi, '')
    .replace(/___json[\s\S]*$/gi, '')
    .replace(/\{\s*"pathname"[\s\S]*$/gi, '')
    .replace(/\s+/g, ' ')
    .trim();

  return text;
}

function getFinalCategory(properties) {
  return (
    properties.final_category_ar ||
    properties.proposed_category_ar ||
    properties.component_category_ar ||
    properties.category_ar ||
    properties.category ||
    ''
  );
}

function getFinalRole(properties) {
  return (
    properties.final_site_role ||
    properties.proposed_site_role ||
    properties.site_role ||
    ''
  );
}

function approvalLabel(properties) {
  const status = properties.approval_status || '';

  if (status === 'pending_review') {
    return 'قيد المراجعة';
  }

  if (status === 'approved_primary') {
    return 'موقع رئيسي معتمد';
  }

  if (status === 'approved_ready') {
    return 'معتمد';
  }

  return '';
}

function heritagePolygonStyle(feature, cfg) {
  if (cfg.id === 'investment') {
    const color = investmentColor(feature, cfg.color);
    return { color, weight: 2, opacity: 0.9, fillColor: color, fillOpacity: 0.1,
      dashArray: feature?.properties?.data_review_status === 'review_required' ? '7 5' : null };
  }
  const pending =
    feature?.properties?.approval_status === 'pending_review';

  return {
    color: pending ? '#d97706' : cfg.color,
    weight: pending ? 2.5 : 2,
    opacity: 0.95,
    fillColor: pending ? '#f59e0b' : cfg.color,
    fillOpacity: pending ? 0.12 : 0.09,
    dashArray: pending ? '7 5' : null
  };
}

function eachAtlasFeature(container, callback) {
  if (!container || typeof container.eachLayer !== 'function') {
    return;
  }

  container.eachLayer(layer => {
    if (layer.feature) {
      callback(layer);
      return;
    }

    if (typeof layer.eachLayer === 'function') {
      eachAtlasFeature(layer, callback);
    }
  });
}

function buildHeritageHierarchy(heritageState) {
  const container = document.getElementById('heritageHierarchy');

  if (!container || !heritageState?.siteLayers) {
    return;
  }

  const preferredOrder = [
    'WH-LY-001',
    'WH-LY-002',
    'WH-LY-003',
    'WH-LY-004',
    'WH-LY-005',
    'MASTER'
  ];

  const siteIds = Object.keys(heritageState.siteLayers).sort(
    (a, b) =>
      preferredOrder.indexOf(a) - preferredOrder.indexOf(b)
  );

  container.innerHTML = siteIds.map(siteId => {
    const info = heritageState.siteInfo[siteId];
    const reviewText = info.pendingReview
      ? `<small>${info.pendingReview.toLocaleString('ar')} قيد المراجعة</small>`
      : '';

    return `
      <label class="heritage-site-row">
        <input
          type="checkbox"
          data-heritage-site="${escapeAttribute(siteId)}"
          checked
        >
        <span class="heritage-site-name">
          ${escapeHtml(info.name)}
          ${reviewText}
        </span>
        <span class="heritage-site-count">
          ${info.total.toLocaleString('ar')}
        </span>
      </label>
    `;
  }).join('');

  container.hidden = false;

  container.querySelectorAll('[data-heritage-site]').forEach(input => {
    input.addEventListener('change', event => {
      toggleHeritageSite(
        event.target.dataset.heritageSite,
        event.target.checked
      );
    });
  });
}

function cleanPopup(
  layer,
  cfg,
  placemark = '',
  kmlFileUrl = ''
) {
  const parsed = placemark
    ? extractPlacemarkProperties(
        placemark,
        kmlFileUrl
      )
    : {};

  const featureProps =
    layer.feature?.properties || {};

  const properties = {
    ...parsed,
    ...featureProps
  };

  const firstValue = (...values) =>
    values.find(value =>
      value !== undefined &&
      value !== null &&
      String(value).trim() !== ''
    ) || '';

  const name = firstValue(
    properties.name_ar,
    properties.nameAr,
    properties.name,
    properties.source_name_ar,
    properties.name_en,
    properties.nameEn,
    'موقع سياحي'
  );

  const rawDescription = firstValue(
    properties.description_ar,
    properties.description,
    properties.description?.value,
    properties.popupinfo,
    properties.PopupInfo
  );

  const publicRightsStatuses = new Set([
    'center_owned',
    'ministry_owned',
    'government_owned',
    'official_partner_permission',
    'photographer_permission',
    'open_license_documented',
    'public_domain_documented'
  ]);

  const imagePublicationPermission =
    properties.image_publication_status ||
    properties.publication_permission ||
    '';

  const imageRightsStatus =
    properties.image_rights_status || '';

  const imageAllowedForMode = INTERNAL_ADMIN_MODE
    ? ['public', 'internal_only'].includes(imagePublicationPermission)
    : imagePublicationPermission === 'public' &&
      publicRightsStatuses.has(imageRightsStatus);

  const localImages = imageAllowedForMode && Array.isArray(properties.local_images)
    ? properties.local_images.filter(path =>
        typeof path === 'string' &&
        !/^(?:[a-z]+:)?\/\//i.test(path) &&
        !path.startsWith('data:') &&
        !path.startsWith('blob:')
      )
    : [];

  const mediaValues = imageAllowedForMode ? [
    properties.external_images,
    properties.images,
    properties.photos,
    properties.photo,
    properties.image,
    properties.images_json
  ] : [];

  const directMedia = [];

  for (const value of mediaValues) {
    if (!value) {
      continue;
    }

    if (Array.isArray(value)) {
      directMedia.push(...value);
      continue;
    }

    if (typeof value === 'string') {
      const trimmed = value.trim();

      if (
        trimmed.startsWith('[') &&
        trimmed.endsWith(']')
      ) {
        try {
          const parsedImages =
            JSON.parse(trimmed);

          if (Array.isArray(parsedImages)) {
            directMedia.push(
              ...parsedImages
            );

            continue;
          }
        } catch {
          // Keep processing as a normal value.
        }
      }

      directMedia.push(trimmed);
    }
  }

  const kmlMedia = imageAllowedForMode && placemark
    ? extractPlacemarkImages(
        placemark,
        properties,
        kmlFileUrl
      )
    : [];

  const photoPaths = [
    ...localImages,
    ...directMedia,
    ...kmlMedia
  ]
    .map(path =>
      normalizeMediaUrl(
        path,
        kmlFileUrl
      )
    )
    .filter(Boolean)
    .filter(
      (path, index, values) =>
        values.indexOf(path) === index
    )
    .slice(0, 6);

  const cleanText =
    cleanGeoJsonDescription(
      cleanDescriptionText(
        rawDescription
      )
    );

  const detailsData = [
    [
      'الموقع التراثي',
      properties.parent_site_name_ar
    ],
    [
      'التصنيف',
      getFinalCategory(properties)
    ],
    [
      'النوع',
      properties.subcategory_ar ||
      (getFinalRole(properties) === 'primary'
        ? 'الموقع الرئيسي'
        : getFinalRole(properties) === 'service'
          ? 'خدمة تابعة'
          : getFinalRole(properties) === 'route'
            ? 'مسار تابع'
            : getFinalRole(properties) === 'area'
              ? 'منطقة أو حدود'
              : getFinalRole(properties) === 'component'
                ? 'معلم تابع'
                : '')
    ],
    [
      'حالة الاعتماد',
      approvalLabel(properties)
    ],
    [
      'الاسم بالإنجليزية',
      properties.name_en
    ],
    [
      'المدينة أو البلدية',
      firstValue(
        properties.city_ar,
        properties.municipality_ar,
        properties.city,
        properties.municipality
      )
    ],
    [
      'العنوان',
      firstValue(properties.address_ar, properties.address)
    ],
    ['الحي أو المنطقة', properties.district_ar],
    ['نوع المطبخ', properties.cuisine_type_ar],
    ['ساعات العمل', properties.opening_hours],
    ['الخدمات', properties.services_ar],
    ['النجوم', properties.stars],
    ['عدد الغرف', properties.rooms],
    ['عدد الأسرة', properties.beds],
    ['عدد الوحدات', properties.units],
    ['الطاقة الاستيعابية', properties.capacity],
    [
      'الخدمات المتاحة',
      [
        properties.beach_access === true ? 'شاطئ' : '',
        properties.pool_available === true ? 'مسبح' : '',
        properties.restaurant_available === true ? 'مطعم' : '',
        properties.parking_available === true ? 'موقف سيارات' : '',
        properties.family_friendly === true ? 'مناسب للعائلات' : ''
      ].filter(Boolean).join('، ')
    ],
    ['حالة التشغيل', properties.operational_status],
    ['نوع الاستثمار', properties.subcategory_ar],
    ['حالة المشروع', properties.project_status_ar],
    ['المساحة (م²)', properties.site_area_m2],
    ['المساحة (هكتار)', properties.site_area_hectares],
    ['الملكية', firstValue(properties.ownership_type, properties.ownership_entity)],
    ['الجهة المسؤولة', firstValue(properties.implementing_entity, properties.supervising_entity)],
    ['المستثمر أو المشغل', firstValue(properties.investor_name, properties.operator_name)],
    ['القيمة الاستثمارية', firstValue(properties.investment_value, properties.estimated_cost)],
    ['نسبة الإنجاز', properties.completion_percentage],
    ['الوظائف المتوقعة', properties.jobs_expected],
    ['حالة البنية التحتية', properties.infrastructure_status],
    ['الحالة القانونية', properties.legal_status],
    ['الجاهزية الاستثمارية الأولية', properties.investment_readiness_level],
    ['الأولوية الأولية', properties.preliminary_priority_level],
    ['حالة الترخيص', properties.license_status],
    ['حالة البيانات', firstValue(properties.data_review_status, properties.data_quality_status)],
    ['المعرف الوطني', firstValue(properties.canonical_id, properties.id)],
    [
      'الاتصال',
      firstValue(
        properties.phone,
        properties.contact
      )
    ],
    ['الموقع الإلكتروني', properties.website],
    ['مصدر البيانات', properties.source]
  ];

  const details = detailsData
    .filter(([, value]) =>
      value !== undefined &&
      value !== null &&
      String(value).trim() !== ''
    )
    .map(([label, value]) => `
      <div class="popup-detail-row">
        <strong>${escapeHtml(label)}:</strong>
        <span>${escapeHtml(String(value))}</span>
      </div>
    `)
    .join('');

  const gallery = photoPaths.length
    ? `
      <div class="popup-gallery">
        ${photoPaths
          .map((path, index) => `
            <button
              type="button"
              class="popup-image-button ${
                index === 0
                  ? 'popup-image-main'
                  : ''
              }"
              data-image="${escapeAttribute(path)}"
              aria-label="عرض صورة الموقع"
            >
              <span class="popup-image-loader"></span>
              <img
                src="${escapeAttribute(path)}"
                alt="${escapeAttribute(name)} - صورة ${index + 1}"
                loading="lazy"
                decoding="async"
                referrerpolicy="no-referrer"
              >
            </button>
          `)
          .join('')}
        ${photoPaths.length > 1 ? `
          <div class="popup-gallery-controls" role="group" aria-label="التنقل بين صور الموقع">
            <button type="button" class="popup-gallery-prev" aria-label="الصورة السابقة">‹</button>
            <span class="popup-gallery-counter" aria-live="polite">1 / ${photoPaths.length}</span>
            <button type="button" class="popup-gallery-next" aria-label="الصورة التالية">›</button>
          </div>
        ` : ''}
      </div>
    `
    : `
      <div class="popup-gallery">
        <div
          class="popup-image-button popup-image-main popup-placeholder-only"
          aria-label="صورة غير متاحة"
        >
          <img
            src="${escapeAttribute(PLACEHOLDER_IMAGE)}"
            alt="${escapeAttribute(name)} - صورة غير متاحة"
            loading="lazy"
            decoding="async"
            data-placeholder="true"
            class="is-loaded"
          >
        </div>
      </div>
    `;

  layer.bindPopup(
    `
      <article
        class="tourism-popup"
        dir="rtl"
      >
        ${gallery}

        <div class="popup-body">
          ${
            approvalLabel(properties)
              ? `
                <span class="popup-approval-badge ${
                  properties.approval_status === 'pending_review'
                    ? 'is-review'
                    : 'is-approved'
                }">
                  ${escapeHtml(approvalLabel(properties))}
                </span>
              `
              : ''
          }
          <h3 class="popup-title">
            ${escapeHtml(String(name))}
          </h3>

          ${properties.investment_readiness_level === 'insufficient_data' ? `
            <div class="popup-investment-warning">
              التقييم أولي ويعكس اكتمال البيانات المتاحة، ولا يمثل اعتمادًا قانونيًا أو قرارًا استثماريًا.
            </div>
          ` : ''}

          ${['review_required', 'pending_review'].includes(properties.data_review_status) ? `
            <div class="popup-data-review-warning">هذا السجل يحتاج مراجعة وتحققًا مؤسسيًا قبل الاعتماد.</div>
          ` : ''}

          ${['internal_only', 'withheld_pending_verification'].includes(properties.publication_status) ? `
            <div class="popup-data-review-warning">سجل للاستخدام الداخلي فقط؛ لم يكتمل التحقق المؤسسي ولا يمثل اعتمادًا رسميًا.</div>
          ` : ''}

          ${details}

          <div class="popup-description">
            ${
              cleanText ||
              'لا يتوفر وصف تفصيلي لهذا الموقع حاليًا.'
            }
          </div>

          <div class="popup-source">
            ${escapeHtml(cfg.name)}
            · أطلس ليبيا السياحي
          </div>
        </div>
      </article>
    `,
    {
      maxWidth: 440,
      minWidth: 300,
      className: 'atlas-popup'
    }
  );

  layer.on('popupopen', event => {
    const container =
      event.popup.getElement();

    if (!container) {
      return;
    }

    const galleryElement =
      container.querySelector(
        '.popup-gallery'
      );

    const buttons = [
      ...container.querySelectorAll(
        '.popup-image-button:not(.popup-placeholder-only)'
      )
    ];

    let settled = 0;
    let loaded = 0;

    const finish = successful => {
      settled += 1;

      if (successful) {
        loaded += 1;
      }

      if (
        settled === buttons.length &&
        loaded === 0 &&
        galleryElement
      ) {
        galleryElement.innerHTML = `
          <div
            class="popup-image-button popup-image-main popup-placeholder-only"
            aria-label="صورة غير متاحة"
          >
            <img
              src="${escapeAttribute(PLACEHOLDER_IMAGE)}"
              alt="${escapeAttribute(name)} - صورة غير متاحة"
              loading="lazy"
              decoding="async"
              data-placeholder="true"
              class="is-loaded"
            >
          </div>
        `;
      }
    };

    buttons.forEach(button => {
      const img =
        button.querySelector('img');

      const loader =
        button.querySelector(
          '.popup-image-loader'
        );

      const mark = successful => {
        if (
          !img ||
          img.dataset.settled === '1'
        ) {
          return;
        }

        img.dataset.settled = '1';

        if (successful) {
          img.classList.add('is-loaded');
          loader?.remove();
          finish(true);
        } else {
          button.remove();
          finish(false);
        }
      };

      img?.addEventListener(
        'load',
        () => mark(true),
        { once: true }
      );

      img?.addEventListener(
        'error',
        () => mark(false),
        { once: true }
      );

      if (img?.complete) {
        queueMicrotask(() =>
          mark(img.naturalWidth > 0)
        );
      }

      button.addEventListener(
        'click',
        event => {
          event.preventDefault();
          event.stopPropagation();

          if (
            img?.dataset.settled === '1' &&
            img.naturalWidth > 0
          ) {
            openAtlasImage(
              button.dataset.image || ''
            );
          }
        }
      );
    });

    if (buttons.length > 1) {
      let activeIndex = 0;
      const counter = container.querySelector('.popup-gallery-counter');
      const showImage = index => {
        activeIndex = (index + buttons.length) % buttons.length;
        buttons.forEach((button, buttonIndex) => {
          button.classList.toggle('popup-image-main', buttonIndex === activeIndex);
          button.hidden = buttonIndex !== activeIndex;
        });
        if (counter) counter.textContent = `${activeIndex + 1} / ${buttons.length}`;
      };
      container.querySelector('.popup-gallery-prev')?.addEventListener('click', () => showImage(activeIndex - 1));
      container.querySelector('.popup-gallery-next')?.addEventListener('click', () => showImage(activeIndex + 1));
      showImage(0);
    }
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
    props.local_images,
    props.external_images,
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
  const value = String(path || '')
    .replaceAll('\\', '/')
    .trim();

  if (!value) {
    return '';
  }

  if (
    value.startsWith('data:') ||
    value.startsWith('blob:') ||
    /^https?:\/\//i.test(value)
  ) {
    return value;
  }

  if (
    value.startsWith('assets/') ||
    value.startsWith('/assets/')
  ) {
    return value.replace(/^\/+/, '');
  }

  if (
    value.startsWith('LIBYA/') ||
    value.startsWith('/LIBYA/')
  ) {
    return `assets/media/${
      value.replace(/^\/+/, '')
    }`;
  }

  return AtlasMediaUtils.normalizeMediaUrl(
    value,
    kmlFileUrl
  );
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
  const existing = state[cfg.id];

  if (!on) {
    if (existing?.group) {
      map.removeLayer(existing.group);
      updateStats();
    }

    if (cfg.id === 'heritage') {
      const hierarchy = document.getElementById('heritageHierarchy');
      if (hierarchy) hierarchy.hidden = true;
    }

    return;
  }

  if (existing?.group) {
    existing.group.addTo(map);

    if (cfg.id === 'heritage') {
      const hierarchy = document.getElementById('heritageHierarchy');
      if (hierarchy) hierarchy.hidden = false;
    }

    fit(existing.group);
    updateStats();
    return;
  }

  beginLoading();

  try {
    if (cfg.type === 'geojson') {
      const response = await fetch(cfg.url);

      if (!response.ok) {
        throw new Error(`GeoJSON ${response.status}: ${cfg.url}`);
      }

      const data = await response.json();
      const pointCluster = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 48
      });
      const shapeGroup = L.featureGroup();
      const compositeGroup = L.featureGroup([
        pointCluster,
        shapeGroup
      ]);

      let count = 0;
      const siteLayers = {};
      const siteInfo = {};

      L.geoJSON(data, {
        filter: feature =>
          (cfg.filter === 'natural' ? naturalFeature(feature) : true) &&
          (INTERNAL_ADMIN_MODE || feature.properties?.publication_status !== 'withheld_pending_verification'),

        pointToLayer: (feature, latLng) =>
          L.marker(latLng, {
            icon: markerIcon(cfg, feature)
          }),

        style: feature =>
          heritagePolygonStyle(feature, cfg),

        onEachFeature: (feature, leafletLayer) => {
          cleanPopup(leafletLayer, cfg);

          const isPoint =
            feature.geometry?.type === 'Point';

          leafletLayer.__atlasContainer =
            isPoint ? pointCluster : shapeGroup;

          leafletLayer.__atlasSiteId =
            feature.properties?.parent_site_id || 'UNASSIGNED';

          leafletLayer.__atlasSiteName =
            feature.properties?.parent_site_name_ar ||
            'غير مصنف';

          leafletLayer.__atlasApprovalStatus =
            feature.properties?.approval_status || '';

          leafletLayer.__atlasContainer.addLayer(leafletLayer);

          const siteId = leafletLayer.__atlasSiteId;

          if (!siteLayers[siteId]) {
            siteLayers[siteId] = [];
            siteInfo[siteId] = {
              name: leafletLayer.__atlasSiteName,
              total: 0,
              pendingReview: 0
            };
          }

          siteLayers[siteId].push(leafletLayer);
          siteInfo[siteId].total += 1;

          if (
            leafletLayer.__atlasApprovalStatus ===
            'pending_review'
          ) {
            siteInfo[siteId].pendingReview += 1;
          }

          count += 1;
        }
      });

      state[cfg.id] = {
        group: compositeGroup,
        pointCluster,
        shapeGroup,
        siteLayers,
        siteInfo,
        count,
        visibleCount: count
      };

      const countBadge = document.querySelector(`[data-layer-count="${cfg.id}"]`);
      if (countBadge) countBadge.textContent = count.toLocaleString('ar');

      compositeGroup.addTo(map);

      if (cfg.id === 'heritage') {
        buildHeritageHierarchy(state[cfg.id]);
      }

      fit(compositeGroup);
      updateStats();
    } else {
      const cluster = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 48
      });

      let count = 0;
      const kmlFileUrl = resolveAssetPath(cfg.file);
      const response = await fetch(kmlFileUrl);

      if (!response.ok) {
        throw new Error(`KML ${response.status}: ${cfg.file}`);
      }

      const kmlText = await response.text();
      const xml = new DOMParser().parseFromString(
        kmlText,
        'application/xml'
      );

      if (xml.querySelector('parsererror')) {
        throw new Error(`Invalid KML XML: ${cfg.file}`);
      }

      const placemarks = [
        ...xml.getElementsByTagNameNS('*', 'Placemark')
      ];

      const parser = omnivore.kml.parse(
        kmlText,
        null,
        L.geoJSON(null, {
          pointToLayer: (feature, latLng) =>
            L.marker(latLng, {
              icon: markerIcon(cfg)
            })
        })
      );

      let index = 0;

      parser.eachLayer(leafletLayer => {
        cleanPopup(
          leafletLayer,
          cfg,
          placemarks[index] || '',
          kmlFileUrl
        );

        cluster.addLayer(leafletLayer);
        index += 1;
        count += 1;
      });

      state[cfg.id] = {
        group: cluster,
        count,
        visibleCount: count
      };

      const countBadge = document.querySelector(`[data-layer-count="${cfg.id}"]`);
      if (countBadge) countBadge.textContent = count.toLocaleString('ar');

      cluster.addTo(map);
      fit(cluster);
      updateStats();
    }
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
      visible += Number.isFinite(value.visibleCount)
        ? value.visibleCount
        : value.count || 0;
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

  const hierarchy = document.getElementById('heritageHierarchy');
  if (hierarchy) {
    hierarchy.hidden = true;
  }

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

function toggleHeritageSite(
  siteId,
  visible
) {
  const heritageState = state.heritage;

  if (
    !heritageState ||
    !heritageState.group ||
    !heritageState.siteLayers
  ) {
    return;
  }

  const layers = heritageState.siteLayers[siteId] || [];

  for (const leafletLayer of layers) {
    const target = leafletLayer.__atlasContainer;

    if (!target) {
      continue;
    }

    if (visible) {
      if (!target.hasLayer(leafletLayer)) {
        target.addLayer(leafletLayer);
      }
    } else if (target.hasLayer(leafletLayer)) {
      target.removeLayer(leafletLayer);
    }
  }

  heritageState.visibleCount =
    Object.values(heritageState.siteLayers)
      .flat()
      .filter(layer =>
        layer.__atlasContainer?.hasLayer(layer)
      )
      .length;

  updateStats();
}

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

    eachAtlasFeature(value.group, layer => {
      if (found) {
        return;
      }

      const props =
        layer.feature?.properties || {};

      const searchable = [
        props.id,
        props.canonical_id,
        ...(Array.isArray(props.legacy_ids) ? props.legacy_ids : []),
        ...(Array.isArray(props.alias_ids) ? props.alias_ids : []),
        props.name_ar,
        props.source_name_ar,
        props.name,
        props.ar_name,
        props.name_en,
        props.en_name,
        props.parent_site_name_ar,
        props.final_category_ar,
        props.proposed_category_ar,
        props.description_ar,
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
      if (
        found.__atlasContainer &&
        typeof found.getLatLng === 'function' &&
        typeof found.__atlasContainer.zoomToShowLayer === 'function'
      ) {
        found.__atlasContainer.zoomToShowLayer(
          found,
          () => found.openPopup()
        );
        return;
      }

      if (typeof found.getLatLng === 'function') {
        map.setView(found.getLatLng(), 14);
      } else if (
        typeof found.getBounds === 'function'
      ) {
        map.fitBounds(found.getBounds(), {
          maxZoom: 14
        });
      }

      setTimeout(() => found.openPopup(), 0);
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
