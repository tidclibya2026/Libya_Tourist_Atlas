# GeoAI API Contract (Future)

Phase 1 is local-only. No request is made to this contract today.

## Endpoint

`POST /api/geoai/query`

## Input

```json
{
  "query": "show hotels",
  "language": "en",
  "map_state": {"center": [32.88, 13.19], "zoom": 7, "active_layers": ["hotels"]},
  "selected_feature": null,
  "active_layers": ["hotels"]
}
```

## Output

```json
{
  "answer": "Found 528 hotel records in the current atlas data.",
  "actions": [{"action": "show_layer", "layer": "hotels"}],
  "sources": ["data/layers/hotels.geojson"],
  "confidence": "high"
}
```

## Future architecture

Frontend → GeoAI Gateway → Tourism Data Retrieval → GeoJSON / Tourism DB / Indicators → LLM → Structured Actions

The gateway must enforce: no invented features, coordinates or counts; no dataset mutation; no unsupported layer action; and no exposure of private image paths.
