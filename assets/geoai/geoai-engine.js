(function (global) {
  function query(text, handlers) { global.AtlasGeoAIContext.setQuery(text); const intent = global.AtlasGeoAIProvider.query(text); return { intent, result: global.AtlasGeoAIActions.execute(intent.action, intent, handlers) }; }
  global.AtlasGeoAI = { provider: 'local', query, allowedActions: [...global.AtlasGeoAIActions.allowed] };
})(window);
