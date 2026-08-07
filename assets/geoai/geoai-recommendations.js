(function (global) {
  function recommend(selected, features, limit = 6) {
    if (!selected) return [];
    return (features || []).filter(item => item.id !== selected.id).map(item => {
      let score = 0;
      if (item.layerId === selected.layerId) score += 3;
      if (item.category && item.category === selected.category) score += 2;
      if (item.municipality && item.municipality === selected.municipality) score += 2;
      if (item.hasImage) score += 1;
      return { ...item, score };
    }).sort((a, b) => b.score - a.score).slice(0, limit);
  }
  global.AtlasGeoAIRecommendations = { recommend };
})(window);
