(function (global) {
  const provider = { name: 'local', query(query) { return global.AtlasGeoAIIntents.parse(query, global.AtlasGeoAIContext.get().language); } };
  global.AtlasGeoAIProvider = provider;
})(window);
