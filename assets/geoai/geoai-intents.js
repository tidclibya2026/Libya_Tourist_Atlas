(function (global) {
  'use strict';
  const patterns = [
    { re: /^(?:اعرض|أظهر|اظهر)\s+(?:ال)?فنادق(?:\s+في\s+(.+))?$/i, intent: 'show_layer', action: 'show_layer', layer: 'hotels', cityGroup: 1 },
    { re: /^(?:اخف|أخف)\s+(?:ال)?فنادق$/i, intent: 'hide_layer', action: 'hide_layer', layer: 'hotels' },
    { re: /^(?:اعرض|أظهر|اظهر)\s+(?:مواقع\s+)?التراث(?:\s+العالمي)?$/i, intent: 'show_layer', action: 'show_layer', layer: 'heritage' },
    { re: /^(?:اعرض|أظهر|اظهر|استكشف)\s+أكاكوس$/i, intent: 'show_layer', action: 'show_layer', layer: 'akakus' },
    { re: /^(?:اعرض|أظهر|اظهر)\s+(?:فرص\s+)?الاستثمار$/i, intent: 'show_layer', action: 'show_layer', layer: 'investment' },
    { re: /^(?:اعرض|أظهر|اظهر)\s+(?:مواقع\s+)?طرابلس$/i, intent: 'search_features', action: 'search_features', city: 'طرابلس' },
    { re: /^(?:ابحث عن|ابحث)\s+(.+)$/i, intent: 'search_features', action: 'search_features', queryGroup: 1 },
    { re: /^(.+?)\s+في\s+طرابلس$/i, intent: 'search_features', action: 'search_features', queryGroup: 1, city: 'طرابلس' },
    { re: /^(?:المواقع\s+القريبة|ما\s+المواقع\s+القريبة؟?)$/i, intent: 'show_nearby', action: 'show_nearby' },
    { re: /^(?:امسح|إمسح)\s*(?:الفلاتر)?$/i, intent: 'clear_filters', action: 'clear_filters' },
    { re: /^show\s+hotels(?:\s+in\s+(.+))?$/i, intent: 'show_layer', action: 'show_layer', layer: 'hotels', cityGroup: 1 },
    { re: /^hide\s+hotels$/i, intent: 'hide_layer', action: 'hide_layer', layer: 'hotels' },
    { re: /^show\s+(?:world\s+)?heritage$/i, intent: 'show_layer', action: 'show_layer', layer: 'heritage' },
    { re: /^show\s+akakus$/i, intent: 'show_layer', action: 'show_layer', layer: 'akakus' },
    { re: /^show\s+investment$/i, intent: 'show_layer', action: 'show_layer', layer: 'investment' },
    { re: /^places\s+in\s+tripoli$/i, intent: 'search_features', action: 'search_features', city: 'Tripoli' },
    { re: /^find\s+(.+)$/i, intent: 'search_features', action: 'search_features', queryGroup: 1 },
    { re: /^hotels\s+in\s+tripoli$/i, intent: 'search_features', action: 'search_features', query: 'hotels', city: 'Tripoli' },
    { re: /^nearby\s+places$/i, intent: 'show_nearby', action: 'show_nearby' },
    { re: /^clear\s+filters$/i, intent: 'clear_filters', action: 'clear_filters' }
  ];
  function parse(query, language) {
    const value = String(query || '').trim();
    for (const item of patterns) {
      const match = value.match(item.re);
      if (!match) continue;
      return { intent: item.intent, action: item.action, layer: item.layer || '', query: item.query || (item.queryGroup ? match[item.queryGroup] : ''), city: item.city || (item.cityGroup ? match[item.cityGroup] || '' : ''), municipality: '', category: '', radius_km: 10, confidence: item.layer || item.queryGroup || item.query ? 'high' : 'medium', language: language || (/[؀-ۿ]/.test(value) ? 'ar' : 'en') };
    }
    return { intent: 'unknown', action: 'show_summary', layer: '', query: value, city: '', municipality: '', category: '', radius_km: 10, confidence: 'low', language: language || 'ar' };
  }
  global.AtlasGeoAIIntents = { parse };
})(window);
