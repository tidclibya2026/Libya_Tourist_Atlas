# World Heritage KML Difference Report

Current source: `data/kml/world-heritage.kml`
New source: `data/incoming/world-heritage-team-update.kml`

- Current GeoJSON features before merge: 207
- New KML placemarks: 299
- Leptis new source placemarks: 111
- Unnamed Leptis excluded after Unicode normalization: 42
- Existing features preserved: 207
- Matched/enriched: 203
- New named features added: 54
- Service/facility additions: 8
- Review-required named additions: 0

Unnamed Leptis records are excluded from GeoJSON, review, and published layers by project decision.

## Validated merge output

- Final GeoJSON features: 261
- Leptis final features: 67
- Cyrene final features: 66
- Ghadames final features: 32
- Sabratha final features: 46
- Akakus final features: 48
- `LEPTIS_UNNAMED_EXCLUDED`: 42
- `LEPTIS_UNNAMED_IN_FINAL_GEOJSON`: 0
- `LEPTIS_UNNAMED_IN_REVIEW`: 0
- `NO_EXISTING_FEATURES_REMOVED`: PASS
- `NO_EXISTING_COORDINATES_CHANGED`: PASS
- `EXISTING_IMAGE_LINKS_UNCHANGED`: PASS
- `WORLD_HERITAGE_ENRICHMENT_VALID`: PASS

The original incoming KML remains untouched.
