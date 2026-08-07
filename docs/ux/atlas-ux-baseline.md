# Atlas UX + GeoAI Phase 1 — Baseline

## CURRENT_UI_STRUCTURE

- A single static `index.html` shell with a top bar, a right-to-left sidebar, Leaflet map workspace, layer toggles, search, counters, and Leaflet popups.
- Runtime layers are configured in `assets/app.js` and loaded from local GeoJSON/KML sources; layer media is read from `data/layer-media.json`.
- Existing image handling, popup galleries, local Leaflet runtime, and offline-safe validation are already established.

## CURRENT_UX_STRENGTHS

- Local Leaflet and MarkerCluster assets avoid a CDN dependency.
- Existing GeoJSON feature IDs and image governance metadata are preserved.
- Popup media uses lazy loading, placeholders, and a local image viewer.
- Heritage hierarchy and institutional review indicators are already represented.

## CURRENT_UX_WEAKNESSES

- The visual hierarchy is utilitarian rather than premium and the brand identity is not explicit.
- Search is confined to the sidebar and returns the first match rather than a contextual result set.
- Layer controls are a flat list without functional grouping or active-layer summaries.
- There is no local natural-language assistant, nearby workflow, or recommendation surface.

## MAP_UX_PROBLEMS

- The map is the primary workspace, but surrounding controls do not clearly explain the current context.
- Base-map availability and data availability are not presented as separate states.

## SEARCH_UX_PROBLEMS

- No debounce, no result cards, and no explicit support for Arabic/English intent queries.
- Search requires a layer to be loaded before a feature can be found.

## POPUP_UX_PROBLEMS

- Feature metadata is dense and actions are not grouped into a clear hierarchy.
- Layer context media is not surfaced as a separate layer-level concept.

## LAYER_CONTROL_PROBLEMS

- Counts are shown only after loading and the list does not communicate categories or media availability consistently.

## MOBILE_PROBLEMS

- The sidebar is a translated panel, but there is no dedicated bottom sheet or persistent floating search/assistant affordance.

## RTL_PROBLEMS

- Arabic is supported at document level, but the interface lacks a deliberate bilingual switch and mirrored navigation semantics.

## VISUAL_IDENTITY_PROBLEMS

- The previous shell uses a generic gradient and does not expose the requested navy/royal/electric blue and warm gold system.
- No tracked Atlas logo asset was found locally; the redesign therefore uses a restrained typographic brand lockup and records the absence rather than substituting another image.

## PERFORMANCE_CONCERNS

- Search should avoid repeated full-DOM scans and media should remain lazy.
- GeoJSON must remain cached in the existing runtime state.

## AI_INTEGRATION_POINTS

- The existing layer registry, loaded feature state, map instance, and popup lifecycle provide a safe local action boundary.
- Phase 1 can implement deterministic intent parsing, nearby calculations, and recommendations without network calls or dataset mutation.
