const layers = [
 {id:'heritage',name:'مواقع التراث العالمي',file:'data/kml/world-heritage.kml',icon:'🏛️',color:'#7c3aed',meta:'التراث العالمي والصور المرتبطة'},
 {id:'akakus',name:'تادرارت أكاكوس والفن الصخري',file:'data/kml/akakus.kml',icon:'🪨',color:'#b45309',meta:'الفن الصخري والمشهد الصحراوي'},
 {id:'oldTripoli',name:'المدينة القديمة طرابلس',file:'data/kml/old-tripoli.kml',icon:'🕌',color:'#0891b2',meta:'المعالم التاريخية داخل المدينة'},
 {id:'hotels',name:'الفنادق',file:'data/kml/hotels.kml',icon:'🏨',color:'#dc2626',meta:'منشآت الإيواء السياحي'},
 {id:'resorts',name:'القرى والمنتجعات السياحية',file:'data/kml/resorts.kml',icon:'🏖️',color:'#0d9488',meta:'القرى والمنتجعات والشاليهات'},
 {id:'investment',name:'المشاريع وفرص الاستثمار',file:'data/kml/investment.kml',icon:'📈',color:'#ca8a04',meta:'مواقع التنمية والفرص الاستثمارية'},
 {id:'naturalGithub',name:'أطلس الموارد الطبيعية – GitHub',type:'geojson',url:'https://raw.githubusercontent.com/tidclibya/libyan--map/main/mapatlas.geojson',filter:'natural',icon:'🌿',color:'#15803d',meta:'ربط مباشر بالمصدر المنشور على GitHub'},
 {id:'national',name:'السجل الوطني الموحد',file:'data/kml/national-atlas.kml',icon:'🇱🇾',color:'#1d4ed8',meta:'24,454 سجلًا – يحمّل عند الطلب'}
];
const map=L.map('map',{zoomControl:true,minZoom:4}).setView([27.2,17.2],5);
const base={
 'خريطة فاتحة':L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{maxZoom:19,attribution:'© OpenStreetMap © CARTO'}),
 'قمر صناعي':L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Tiles © Esri'})
};base['خريطة فاتحة'].addTo(map);L.control.layers(base,null,{position:'topleft'}).addTo(map);
const state={};let totalVisible=0;let loadingRequests=0;
const list=document.getElementById('layerList');
for(const cfg of layers){
 const card=document.createElement('div');card.className='layer-card';
 card.innerHTML=`<div class="layer-icon" style="background:${cfg.color}">${cfg.icon}</div><div><div class="layer-name">${cfg.name}</div><div class="layer-meta">${cfg.meta}</div></div><label class="switch"><input type="checkbox" data-id="${cfg.id}"><span></span></label>`;
 list.appendChild(card);card.querySelector('input').addEventListener('change',e=>toggleLayer(cfg,e.target.checked));
}
function markerIcon(cfg){return L.divIcon({className:'',html:`<div style="width:30px;height:30px;border-radius:10px;background:${cfg.color};color:white;display:grid;place-items:center;border:2px solid white;box-shadow:0 3px 9px #0004;font-size:16px">${cfg.icon}</div>`,iconSize:[30,30],iconAnchor:[15,15]});}
function cleanPopup(layer, cfg) {
    const props = layer.feature?.properties || {};

    const name = props.name || 'موقع سياحي';

    let rawDescription =
        props.description?.value ||
        props.description ||
        '';

    if (layer.getPopup()) {
        const originalPopup = layer.getPopup().getContent();

        if (originalPopup) {
            rawDescription = originalPopup;
        }
    }

    const safeDescription = sanitizeKmlDescription(
        String(rawDescription)
    );

    const popupContent = `
        <article class="tourism-popup" dir="rtl">
            <div class="popup-gallery">
                ${extractImages(safeDescription)}
            </div>

            <div class="popup-body">
                <h3 class="popup-title">
                    ${escapeHtml(name)}
                </h3>

                <div class="popup-description">
                    ${extractTextContent(safeDescription)}
                </div>

                <div class="popup-source">
                    ${escapeHtml(cfg.name)} · نسخة عرض مؤسسية
                </div>
            </div>
        </article>
    `;

    layer.bindPopup(popupContent, {
        maxWidth: 440,
        minWidth: 300,
        className: 'atlas-popup'
    });
}

function sanitizeKmlDescription(html) {
    return html
        .replace(/<script[\s\S]*?<\/script>/gi, '')
        .replace(/\son\w+\s*=\s*["'][^"']*["']/gi, '')
        .replace(/javascript:/gi, '');
}

function extractImages(html) {
    const documentFragment = new DOMParser().parseFromString(
        html,
        'text/html'
    );

    const images = Array.from(
        documentFragment.querySelectorAll('img')
    );

    if (!images.length) {
        return '';
    }

    return images
        .slice(0, 4)
        .map((image, index) => {
            const source = normalizeImageUrl(
                image.getAttribute('src') || ''
            );

            if (!source) {
                return '';
            }

            return `
                <button
                    type="button"
                    class="popup-image-button"
                    onclick="openAtlasImage('${escapeAttribute(source)}')"
                    aria-label="عرض صورة الموقع"
                >
                    <img
                        src="${escapeAttribute(source)}"
                        alt="صورة ${index + 1}"
                        loading="lazy"
                        referrerpolicy="no-referrer"
                        onerror="this.closest('.popup-image-button').remove()"
                    >
                </button>
            `;
        })
        .join('');
}

function extractTextContent(html) {
    const documentFragment = new DOMParser().parseFromString(
        html,
        'text/html'
    );

    documentFragment
        .querySelectorAll('img, script, style')
        .forEach(element => element.remove());

    const bodyHtml = documentFragment.body.innerHTML.trim();

    return bodyHtml || 'بيانات الموقع ضمن طبقة أطلس ليبيا السياحي.';
}

function normalizeImageUrl(url) {
    if (!url) {
        return '';
    }

    const trimmedUrl = url.trim();

    if (
        trimmedUrl.startsWith('https://') ||
        trimmedUrl.startsWith('http://') ||
        trimmedUrl.startsWith('data:image/')
    ) {
        return trimmedUrl;
    }

    return '';
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

    document.body.appendChild(viewer);
}
function escapeHtml(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function naturalFeature(f){const p=f.properties||{};const t=((p.name||'')+' '+(p.description?.value||p.description||'')).toLowerCase();return ['بحيرة','وادي','جبل','كهف','شاط','جزيرة','سبخة','غابة','طبيع','قوس صخري','شلال','عين','نبع','رمال','كثبان','واحة','محمية','خليج'].some(k=>t.includes(k));}
async function toggleLayer(cfg,on){
 if(!on){if(state[cfg.id]?.group){map.removeLayer(state[cfg.id].group);updateStats();}return;}
 if(state[cfg.id]?.group){state[cfg.id].group.addTo(map);fit(state[cfg.id].group);updateStats();return;}
 beginLoading();
 try{
   const cluster=L.markerClusterGroup({chunkedLoading:true,maxClusterRadius:48});let count=0;
   if(cfg.type==='geojson'){
     const r=await fetch(cfg.url);if(!r.ok)throw new Error('GitHub '+r.status);const data=await r.json();
     L.geoJSON(data,{filter:f=>cfg.filter==='natural'?naturalFeature(f):true,pointToLayer:(f,ll)=>L.marker(ll,{icon:markerIcon(cfg)}),onEachFeature:(f,l)=>{cleanPopup(l,cfg);cluster.addLayer(l);count++;}});
   }else{
     await new Promise((resolve,reject)=>{
       const parser=omnivore.kml(cfg.file,null,L.geoJSON(null,{pointToLayer:(f,ll)=>L.marker(ll,{icon:markerIcon(cfg)}),onEachFeature:(f,l)=>{cleanPopup(l,cfg);count++;}}));
       parser.on('ready',()=>{parser.eachLayer(l=>cluster.addLayer(l));resolve();});parser.on('error',reject);
     });
   }
   state[cfg.id]={group:cluster,count};cluster.addTo(map);fit(cluster);updateStats();
 }catch(e){console.error(e);alert(`تعذر تحميل طبقة: ${cfg.name}`);document.querySelector(`[data-id="${cfg.id}"]`).checked=false;
 }finally{endLoading()}
}
function fit(g){try{const b=g.getBounds();if(b.isValid())map.fitBounds(b.pad(.08),{maxZoom:11});}catch{}}
function updateStats(){let loaded=0,visible=0;for(const v of Object.values(state)){if(v.group&&map.hasLayer(v.group)){loaded++;visible+=v.count||0;}}document.getElementById('loadedCount').textContent=loaded.toLocaleString('ar');document.getElementById('featureCount').textContent=visible.toLocaleString('ar');totalVisible=visible;}
function beginLoading(){
 loadingRequests++;
 const el=document.getElementById('loading');
 el.hidden=false;
}
function endLoading(){
 loadingRequests=Math.max(0,loadingRequests-1);
 const el=document.getElementById('loading');
 el.hidden=loadingRequests===0;
}
document.getElementById('clearBtn').onclick=()=>{document.querySelectorAll('.switch input').forEach(x=>{x.checked=false});Object.values(state).forEach(v=>v.group&&map.removeLayer(v.group));updateStats();};
document.getElementById('searchBtn').onclick=search;document.getElementById('searchInput').addEventListener('keydown',e=>{if(e.key==='Enter')search()});
function search(){const q=document.getElementById('searchInput').value.trim().toLowerCase();if(!q)return;for(const v of Object.values(state)){if(!v.group||!map.hasLayer(v.group))continue;let found=null;v.group.eachLayer(l=>{if(found)return;const n=(l.feature?.properties?.name||'').toLowerCase();if(n.includes(q))found=l;});if(found){map.setView(found.getLatLng(),14);found.openPopup();return;}}alert('لم يُعثر على الموقع داخل الطبقات المحمّلة.');}
document.getElementById('mobileToggle').onclick=()=>document.getElementById('sidebar').classList.toggle('open');
// تحميل طبقة التراث العالمي تلقائيًا كبداية خفيفة
setTimeout(()=>{const x=document.querySelector('[data-id="heritage"]');x.checked=true;toggleLayer(layers[0],true)},350);
