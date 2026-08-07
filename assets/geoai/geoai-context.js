(function (global) {
  const context = { selectedFeature: null, selectedLayer: null, activeLayers: [], mapCenter: null, zoom: null, language: 'ar', lastQuery: '' };
  global.AtlasGeoAIContext = {
    get: () => ({ ...context, activeLayers: [...context.activeLayers] }),
    update(patch) { Object.assign(context, patch || {}); return this.get(); },
    setQuery(query) { context.lastQuery = String(query || ''); },
    setLanguage(language) { context.language = language === 'en' ? 'en' : 'ar'; }
  };
})(window);
