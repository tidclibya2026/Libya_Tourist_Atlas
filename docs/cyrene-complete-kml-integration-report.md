# تكامل قورينا الأثري – شحات

## المصدر والعدد

- KML المرجعي: `data/kml/world-heritage.kml`
- ملف العرض الفعلي: `data/layers/world-heritage.geojson`
- مجلد KML الفعلي: `شحات_`
- الموقع الرئيسي الحالي: `WH-WORLD-C0002` — `موقع قورينا الأثري – شحات`
- `KML_CYRENE_TOTAL = 29` (28 داخل مجلد شحات + الموقع الرئيسي)
- `KML_CYRENE_POINTS = 29`
- `KML_CYRENE_POLYGONS = 0`
- `KML_CYRENE_OTHER_GEOMETRIES = 0`
- `GEOJSON_CYRENE_TOTAL = 29`

تم الحفاظ على ترتيب KML والهندسات والإحداثيات والمعرفات القائمة. الموقع الرئيسي مضبوط على `site_role=primary` و`name_en=Archaeological Site of Cyrene`.

## الصور

مصدر الصور الرسمي الفعلي هو `شحات`، ولم توجد مجلدات أطلس قديمة مستقلة باسم Shahat/Cyrene في المسارات المفحوصة. لذلك:

- `OFFICIAL_CENTER_IMAGES = 46`
- `EXISTING_ATLAS_IMAGES = 0`
- `UNIQUE_IMAGES = 46`
- `DUPLICATE_IMAGES = 0`
- `REVIEW_REQUIRED_IMAGES = 44`
- الصور المؤكدة المنشورة: صورتان جويتان للموقع الرئيسي فقط.
- الصور الـ44 المتبقية محفوظة في `assets/media/LIBYA/heritage/cyrene/published/review-required/` وغير مرتبطة بمعالم فرعية.

لم يُربط أي معبد أو مسرح أو حمام أو متحف بصورة غير مؤكدة اعتمادًا على اسم ملف عام فقط. سجل الجرد الكامل في `docs/media-linkage/cyrene-complete-image-linkage.csv`.

## التحقق

- `KML_TO_GEOJSON_CYRENE_MATCH = PASS`
- `ALL_CYRENE_FEATURES_RENDERED = PASS` (29)
- `CYRENE_MAIN_POPUP = PASS`
- `CYRENE_TEMPLE_ZEUS_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_TEMPLE_APOLLO_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_APOLLO_SANCTUARY_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_GREEK_THEATRE_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_ROMAN_THEATRE_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_AGORA_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_BATHS_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_MUSEUM_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_NECROPOLIS_POPUP = NO_CONFIRMED_IMAGE`
- `CYRENE_IMAGES_HTTP = PASS` (46 صورة منشورة، HTTP 200 وContent-Type صورة)
- `NO_IMAGE_404 = PASS`
- `NO_CONSOLE_ERRORS = PASS`
- `CYRENE_COORDINATES_UNCHANGED = PASS`
- `LEPTIS_FEATURES_UNCHANGED = PASS`
- `SABRATHA_FEATURES_UNCHANGED = PASS`
- `FAILED = 0`

اختبار Playwright: `scripts/test-cyrene-complete-playwright.py` ويغطي الموقع الرئيسي، جميع العناصر، البحث عن زيوس، إخفاء/إظهار المجموعة، popups والطلبات الفاشلة. اختبار البيانات: `scripts/validate-cyrene-complete.mjs`.

## النسخة الاحتياطية

external recovery backup created outside the repository (path recorded in the execution log)

تشمل GeoJSON وJavaScript وCSS وHTML ومجلدات الصور السابقة الموجودة ونسخة المصدر الرسمي.

لم يتم تنفيذ `git commit` أو `git push` أو deploy.

## Actual clicked feature image correction

The feature opened by the map click for “آثار قورينا” is `WH-LY-003-C0005` (not the primary feature `WH-WORLD-C0002`). Its KML geometry and identifier were preserved. The component now uses the two confirmed public main-site images, with institutional ownership metadata, so its popup renders the real gallery instead of the placeholder. Its descriptive fields were normalized without embedding coordinates.

- `CYRENE_SCREENSHOT_FEATURE_ID`: `WH-LY-003-C0005`
- `local_images`: two relative `published/main-site` paths
- overlap with primary marker: no coordinate overlap; separate component retained
