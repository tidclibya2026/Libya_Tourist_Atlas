# تكامل صبراتة الأثري

## المصدر والعدد

- KML: `data/kml/world-heritage.kml`
- GeoJSON المستخدم: `data/layers/world-heritage.geojson`
- مجلد KML: `اثار صبراتة`، 46 Placemark، مع عنصر الموقع الرئيسي `WH-WORLD-C0001`.
- `KML_SABRATHA_TOTAL = 47`
- `KML_SABRATHA_POINTS = 46` (45 داخل المجلد + الموقع الرئيسي)
- `KML_SABRATHA_POLYGONS = 0`
- `KML_SABRATHA_OTHER_GEOMETRIES = 1` (Placemark بلا هندسة، محفوظ في GeoJSON)
- `GEOJSON_SABRATHA_TOTAL = 47`

الموقع الرئيسي الحالي هو `WH-WORLD-C0001`، وتم تحديث دوره إلى `primary` والاسم الإنجليزي إلى `Archaeological Site of Sabratha`. لم يُنشأ معرف جديد.

## الربط المؤكد

- الموقع الرئيسي: 4 صور عامة، منها صورة أطلس سابقة.
- مسرح صبراته الأثري `WH-LY-002-C0042`: 8 صور مسرح.
- الضريح البونيقي `WH-LY-002-C0043`: صورتان.
- متحف روماني `WH-LY-002-C0019`: صورتان لمدخل/مبنى المتحف.
- الامفيثياتر `WH-LY-002-C0045`: صورتان لميدان المصارعة.
- الحمامات، الفورم، المتحف البونيقي والعناصر غير الواضحة بقيت دون صورة مؤكدة وظهرت بالـ placeholder.

الصور الرسمية مصدرها `صبراتة` وتستخدم `official_center_media` و`institutional_ownership`. الصورة القديمة مصدرها `assets/media/LIBYA/Sabratha` وتستخدم `existing_atlas_media` و`existing_project_asset`. عند الموقع الرئيسي استُخدم `official_and_existing_atlas_media`.

## الجرد والنشر

- صور رسمية أصلية: 40
- صور أطلس سابقة أصلية: 1
- صور أصلية فريدة SHA-256: 41
- تكرارات بين المصدرين: 0
- صور مرتبطة بعناصر: 18 مسارًا منشورًا عبر 5 عناصر
- صور قيد المراجعة: 22 نسخة منشورة في `published/review-required`
- سجل الجرد: `docs/media-linkage/sabratha-complete-image-linkage.csv`
- مجلد النشر: `assets/media/LIBYA/Sabratha/published/`

لم تُحذف أو تُستبدل أي صورة أصلية. مسارات `local_images` نسبية ولا تحتوي `file://` أو مسارات Windows أو `review-required`.

## التحقق

- `KML_TO_GEOJSON_SABRATHA_MATCH = PASS`
- `ALL_SABRATHA_FEATURES_RENDERED = PASS` (47 عنصرًا؛ العنصر بلا هندسة محفوظ لكنه غير قابل للرسم كنقطة)
- `SABRATHA_MAIN_POPUP = PASS`
- `SABRATHA_THEATRE_POPUP = PASS`
- `SABRATHA_PUNIC_MAUSOLEUM_POPUP = PASS`
- `SABRATHA_MUSEUM_POPUP = PASS`
- `SABRATHA_BATHS_POPUP = NO_CONFIRMED_IMAGE`
- `SABRATHA_FORUM_POPUP = NO_CONFIRMED_IMAGE`
- `SABRATHA_IMAGES_HTTP = PASS` (41 صورة منشورة، HTTP 200 وContent-Type صورة)
- `NO_IMAGE_404 = PASS`
- `NO_CONSOLE_ERRORS = PASS`
- `LEPTIS_FEATURES_UNCHANGED = PASS`
- `FAILED = 0`

اختبار Playwright: `scripts/test-sabratha-complete-playwright.py`، واختبار البيانات: `scripts/validate-sabratha-complete.mjs`.

## النسخة الاحتياطية

external recovery backup created outside the repository (path recorded in the execution log)

تتضمن ملفات GeoJSON وJavaScript وCSS وHTML ونسخة مجلد صور صبراتة والمصدر الرسمي.

لم يُنفذ `git commit` أو `git push` أو deploy.
