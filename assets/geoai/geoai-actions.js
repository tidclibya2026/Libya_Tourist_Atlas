(function (global) {
  const allowed = new Set(['show_layer', 'hide_layer', 'search_features', 'focus_feature', 'fit_layer', 'filter_layer', 'clear_filters', 'show_summary', 'show_nearby', 'show_recommendations']);
  function execute(action, payload, handlers) { if (!allowed.has(action)) return { ok: false, reason: 'unsupported_action' }; const fn = handlers && handlers[action]; return typeof fn === 'function' ? { ok: true, value: fn(payload || {}) } : { ok: false, reason: 'handler_missing' }; }
  global.AtlasGeoAIActions = { allowed, execute };
})(window);
