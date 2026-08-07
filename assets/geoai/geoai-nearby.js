(function (global) {
  function haversine(a, b) {
    const rad = Math.PI / 180; const dLat = (b[0] - a[0]) * rad; const dLon = (b[1] - a[1]) * rad;
    const x = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * rad) * Math.cos(b[0] * rad) * Math.sin(dLon / 2) ** 2;
    return 6371 * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
  }
  function nearby(origin, features, radiusKm) { return (features || []).map(item => ({ ...item, distance_km: haversine(origin, item.coordinates) })).filter(item => item.distance_km <= radiusKm).sort((a, b) => a.distance_km - b.distance_km); }
  global.AtlasGeoAINearby = { haversine, nearby };
})(window);
