# Batch 1 approval correction

Institutional approval is recorded separately from individual visual verification. All 74 previously published candidates are now provisional; individual review fields are reset to defer/not individually verified. World Heritage links are retained provisionally where IDs exist. Akakus and Old Tripoli candidates are withheld pending actual layer linkage.

Status: BATCH_1_INSTITUTIONAL_APPROVAL_RECORDED
Status: BATCH_1_PENDING_INDIVIDUAL_VISUAL_VERIFICATION

## Local runtime linkage correction

Leaflet and MarkerCluster are not present locally in node_modules, vendor, or assets/vendor. CDN references remain pending local runtime provisioning; no downloads were performed. World Heritage: 5 linked to world-heritage.geojson. Akakus: 9 withheld because no runtime GeoJSON layer was found. Old Tripoli: 60 withheld because no runtime GeoJSON layer was found. Status: BATCH_1_BLOCKED_NO_LOCAL_LEAFLET.

## Offline runtime completion

Leaflet 1.9.4 and MarkerCluster 1.5.3 were installed exactly from registry.npmjs.org and vendored with licenses. Offline Playwright runtime passed with no console errors, page errors, external requests, or 404s. Runtime linkage is 5 World Heritage images; 69 Akakus/Old Tripoli derivatives remain withheld because no runtime GeoJSON layer is loaded. Status: BATCH_1_CORRECTION_COMPLETE_WITH_WITHHELD_LINKS.
