(function () {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const app = window.__atlasTest || {};

  function injectStyle() {
    if ($('#atlasUxStyle')) return;
    const link = document.createElement('link'); link.id = 'atlasUxStyle'; link.rel = 'stylesheet'; link.href = 'assets/atlas-ux-geoai.css'; document.head.appendChild(link);
  }
  function addHeaderAndHero() {
    const topbar = $('.topbar'); if (!topbar) return;
    topbar.classList.add('atlas-header');
    if (!$('.brand-lockup', topbar)) {
      topbar.innerHTML = `<a class="brand-lockup" href="#map" aria-label="أطلس ليبيا السياحي"><span class="brand-mark" aria-hidden="true">✦</span><span class="brand-copy"><strong>أطلس ليبيا السياحي</strong><small>LIBYA TOURISM ATLAS</small></span></a><nav class="primary-nav" aria-label="التنقل الرئيسي"><a href="#map">استكشف</a><a href="#layerList">الطبقات</a><a href="#resultsPanel">الوجهات</a><a href="#layerList">الاستثمار</a><button class="nav-ai-link" id="navAiButton" type="button">اسأل الأطلس</button></nav><div class="header-actions"><button class="language-switch" id="languageSwitch" type="button" aria-label="تبديل اللغة">AR <span>EN</span></button><span class="status"><span></span> تشغيل محلي آمن</span></div>`;
    }
    if (!$('#atlasBrandStrip')) {
      const strip = document.createElement('section'); strip.id = 'atlasBrandStrip'; strip.className = 'brand-strip'; strip.innerHTML = `<div><p class="eyebrow">منصة وطنية للوجهات والطبقات السياحية</p><h1>بوابتك الذكية لاستكشاف ليبيا</h1><p class="brand-subtitle">استكشف المواقع، الخدمات، الإقامة وفرص الاستثمار من خريطة واحدة.</p></div><div class="brand-strip-actions"><button class="button button-primary" id="heroExploreButton" type="button">استكشف الخريطة</button><button class="button button-secondary" id="heroAiButton" type="button">اسأل الأطلس</button></div>`;
      topbar.after(strip);
    }
  }
  function upgradeSearch() {
    const wrap = $('.search-wrap'); const input = $('#searchInput'); if (!wrap || !input) return;
    wrap.classList.add('smart-search'); input.placeholder = 'ابحث عن موقع، مدينة، فندق، تجربة أو اسأل الأطلس...';
    if (!$('.search-icon', wrap)) { const icon = document.createElement('div'); icon.className = 'search-icon'; icon.textContent = '⌕'; icon.setAttribute('aria-hidden', 'true'); wrap.prepend(icon); }
    if (!$('.search-hint', wrap)) { const hint = document.createElement('span'); hint.className = 'search-hint'; hint.textContent = 'Enter'; wrap.appendChild(hint); }
    let timer; input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => renderResults(input.value), 240); });
  }
  function addPanels() {
    if (!$('#resultsPanel')) { const panel = document.createElement('section'); panel.id = 'resultsPanel'; panel.className = 'context-panel'; panel.hidden = true; panel.innerHTML = `<div class="context-panel-heading"><div><span class="section-kicker">نتائج سياقية</span><h2>الوجهات المقترحة</h2></div><button class="text-button" id="closeResults" type="button">إغلاق</button></div><div id="resultsList" class="results-list"></div>`; $('.map-shell')?.after(panel); }
    if (!$('#geoaiButton')) { const button = document.createElement('button'); button.id = 'geoaiButton'; button.className = 'geoai-fab'; button.type = 'button'; button.innerHTML = '<span aria-hidden="true">✦</span> اسأل الأطلس'; $('.map-shell')?.appendChild(button); }
    if (!$('#geoaiPanel')) { const dialog = document.createElement('dialog'); dialog.id = 'geoaiPanel'; dialog.className = 'geoai-panel'; dialog.innerHTML = `<div class="geoai-panel-header"><div><span class="section-kicker">GeoAI · محلي</span><h2>اسأل أطلس ليبيا</h2><p>استكشف المواقع والطبقات والبيانات السياحية باستخدام اللغة الطبيعية.</p></div><button id="geoaiClose" class="dialog-close" type="button" aria-label="إغلاق">×</button></div><div class="quick-prompts"><button type="button" data-prompt="اعرض الفنادق">اعرض الفنادق</button><button type="button" data-prompt="اعرض مواقع التراث العالمي">مواقع التراث العالمي</button><button type="button" data-prompt="استكشف أكاكوس">استكشف أكاكوس</button><button type="button" data-prompt="اعرض فرص الاستثمار">فرص الاستثمار</button><button type="button" data-prompt="المواقع القريبة">المواقع القريبة</button><button type="button" data-prompt="اعرض مواقع طرابلس">مواقع طرابلس</button></div><div id="geoaiMessages" class="geoai-messages" aria-live="polite"><div class="geoai-welcome">مرحبًا، اسألني عن طبقة أو مدينة أو موقع.</div></div><form id="geoaiForm" class="geoai-form"><input id="geoaiInput" type="text" placeholder="اكتب سؤالك..." aria-label="سؤال GeoAI"><button type="submit">إرسال</button></form>`; document.body.appendChild(dialog); }
  }
  function normalizeSearchText(value) {
    return String(value || '').toLowerCase().normalize('NFD').replace(/[\u064B-\u065F\u0670]/g, '').replace(/[إأآ]/g, 'ا').replace(/ى/g, 'ي').replace(/\s+/g, ' ').trim();
  }
  function activeFeatures() {
    if (window.AtlasRuntime?.getAllFeatures) {
      return window.AtlasRuntime.getAllFeatures().map(item => {
        const p = item.feature.feature?.properties || {};
        const ll = typeof item.feature.getLatLng === 'function' ? item.feature.getLatLng() : null;
        return { layer: item.feature, layerId: item.layerId, id: p.id || p.canonical_id || '', name: p.name_ar || p.name || p.name_en || 'موقع سياحي', nameEn: p.name_en || p.en_name || '', category: p.category_ar || p.category || '', municipality: p.municipality_ar || p.city_ar || '', hasImage: Array.isArray(p.local_images) && p.local_images.length > 0, coordinates: ll ? [ll.lat, ll.lng] : null };
      });
    }
    const rows = []; const states = app.state || {};
    for (const [layerId, value] of Object.entries(states)) { if (!value?.group) continue; eachFeature(value.group, layer => { const p = layer.feature?.properties || {}; const ll = typeof layer.getLatLng === 'function' ? layer.getLatLng() : null; rows.push({ layer, layerId, id: p.id || p.canonical_id || '', name: p.name_ar || p.name || p.name_en || 'موقع سياحي', nameEn: p.name_en || p.en_name || '', category: p.category_ar || p.category || '', municipality: p.municipality_ar || p.city_ar || '', hasImage: Array.isArray(p.local_images) && p.local_images.length > 0, coordinates: ll ? [ll.lat, ll.lng] : null }); }); }
    return rows;
  }
  function eachFeature(container, callback) { if (!container?.eachLayer) return; container.eachLayer(layer => { if (layer.feature) callback(layer); else if (layer.eachLayer) eachFeature(layer, callback); }); }
  function showResults(rows) { const panel = $('#resultsPanel'); const list = $('#resultsList'); if (!panel || !list) return; list.innerHTML = rows.slice(0, 12).map((r, i) => `<article class="result-card"><strong>${escapeHtml(r.name)}</strong>${r.nameEn ? `<small>${escapeHtml(r.nameEn)}</small>` : ''}<small>${escapeHtml(r.category || r.layerId)}</small><button type="button" data-result-index="${i}">عرض على الخريطة</button></article>`).join('') || '<div class="geoai-welcome">لا توجد نتائج مطابقة في بيانات الأطلس الحالية.</div>'; panel.hidden = false; list.querySelectorAll('[data-result-index]').forEach(button => button.addEventListener('click', () => { const row = rows[Number(button.dataset.resultIndex)]; if (row?.layer) { if (typeof row.layer.getLatLng === 'function') app.map.setView(row.layer.getLatLng(), 14); row.layer.openPopup(); } })); }
  function renderResults(query, options = {}) { if (!query?.trim()) return []; const q = normalizeSearchText(query); const rows = activeFeatures().filter(r => { const haystack = normalizeSearchText(`${r.id} ${r.name} ${r.nameEn} ${r.category} ${r.municipality} ${r.layerId}`); return haystack.includes(q) && (!options.layer || r.layerId === options.layer); }); showResults(rows); return rows; }
  function escapeHtml(value) { return String(value || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  function toggleLayer(id, on) { if (window.AtlasRuntime) return on ? window.AtlasRuntime.showLayer(id) : window.AtlasRuntime.hideLayer(id); const checkbox = document.querySelector(`[data-id="${id}"]`); if (checkbox && checkbox.checked !== on) { checkbox.checked = on; checkbox.dispatchEvent(new Event('change', { bubbles: true })); } return !!checkbox; }
  function layerName(id) { return (app.layers || []).find(item => item.id === id)?.name || id; }
  function executeIntent(text) {
    const handlers = {
      show_layer: intent => { toggleLayer(intent.layer, true); return `تم تفعيل طبقة ${layerName(intent.layer)}.`; },
      hide_layer: intent => { toggleLayer(intent.layer, false); return `تم إخفاء طبقة ${layerName(intent.layer)}.`; },
      search_features: intent => {
        const query = intent.query || intent.city || text;
        if (intent.query && /فنادق|فندق|hotel/i.test(intent.query)) toggleLayer('hotels', true);
        if (intent.city && /طرابلس|tripoli/i.test(intent.city)) toggleLayer('oldTripoli', true);
        const input = $('#searchInput'); if (input) input.value = query;
        setTimeout(() => renderResults(query, { layer: intent.query && /فنادق|فندق|hotel/i.test(intent.query) ? 'hotels' : undefined }), 650);
        return `أبحث في بيانات الأطلس عن «${query}».`;
      },
      clear_filters: () => { $('#clearBtn')?.click(); return 'تم مسح الفلاتر وإخفاء الطبقات.'; },
      show_nearby: () => window.AtlasRuntime?.getSelectedFeature() ? 'أحسب المواقع القريبة من الموقع المحدد.' : 'اختر موقعًا من الخريطة أولًا.',
      show_summary: () => {
        const query = String(text || '').trim();
        if (query && window.AtlasRuntime?.searchFeatures) {
          const matches = window.AtlasRuntime.searchFeatures(query);
          const rows = matches.map(item => { const p = item.feature.feature?.properties || {}; return { layer: item.feature, layerId: item.layerId, id: p.id, name: p.name_ar || p.name || p.name_en, nameEn: p.name_en || '', category: p.category_ar || p.category || '', municipality: p.municipality_ar || p.city_ar || '' }; });
          showResults(rows);
          return rows.length ? `وجدت ${rows.length.toLocaleString('ar')} نتيجة مرتبطة بـ«${query}».` : 'لم أجد نتائج مطابقة في بيانات الأطلس الحالية.';
        }
        return 'لم أفهم الطلب بشكل كافٍ. جرّب اسم مدينة، طبقة، موقع أو نوعًا سياحيًا.';
      }
    };
    const response = window.AtlasGeoAI.query(text, handlers);
    return response.result.ok ? response.result.value : handlers.show_summary();
  }
  function addMessage(text, type) { const box = $('#geoaiMessages'); if (!box) return; const div = document.createElement('div'); div.className = `geoai-message ${type || ''}`; div.textContent = text; box.appendChild(div); box.scrollTop = box.scrollHeight; }
  function wireInteractions() { const open = () => { const dialog = $('#geoaiPanel'); if (dialog?.showModal) dialog.showModal(); else dialog?.setAttribute('open', ''); }; ['geoaiButton', 'navAiButton', 'heroAiButton'].forEach(id => document.getElementById(id)?.addEventListener('click', open)); $('#heroExploreButton')?.addEventListener('click', () => $('#map')?.scrollIntoView({ behavior: 'smooth' })); $('#geoaiClose')?.addEventListener('click', () => $('#geoaiPanel')?.close()); $('#closeResults')?.addEventListener('click', () => { $('#resultsPanel').hidden = true; }); $$('.quick-prompts button').forEach(button => button.addEventListener('click', () => { addMessage(button.dataset.prompt, 'user'); addMessage(executeIntent(button.dataset.prompt)); })); $('#geoaiForm')?.addEventListener('submit', event => { event.preventDefault(); const input = $('#geoaiInput'); const value = input?.value.trim(); if (!value) return; addMessage(value, 'user'); addMessage(executeIntent(value)); input.value = ''; }); $('#languageSwitch')?.addEventListener('click', () => { const en = document.documentElement.lang !== 'en'; document.documentElement.lang = en ? 'en' : 'ar'; document.documentElement.dir = en ? 'ltr' : 'rtl'; AtlasGeoAIContext.setLanguage(en ? 'en' : 'ar'); }); }
  function boot() { injectStyle(); addHeaderAndHero(); upgradeSearch(); addPanels(); wireInteractions(); window.__atlasUX = { activeFeatures, executeIntent, renderResults, logo: { found: false, path: '' } }; }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true }); else boot();
})();
