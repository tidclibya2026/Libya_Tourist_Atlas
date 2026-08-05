# تكامل طبقة لبدة الكبرى من KML

## المصدر والتحميل

- ملف KML المرجعي الفعلي: `data/kml/world-heritage.kml`.
- النسختان `data/source-kml/world-heritage.kml` و`data/kml/final/world-heritage.kml` متطابقتان معه.
- التطبيق في `index.html` يحمل `assets/app.js`، وطبقة التراث في `assets/app.js` تستخدم فقط `data/layers/world-heritage.geojson`. ملف `world-heritage-components.geojson` قديم وغير محمّل.
- أُنشئت نسخة احتياطية قبل التعديل في external recovery backup created outside the repository (path recorded in the execution log).

## مطابقة العدد

| المؤشر | القيمة |
|---|---:|
| KML_TOTAL | 207 |
| KML_LEPTIS_TOTAL | 53 (الموقع الرئيسي + 52 Placemark داخل مجلد لبدة) |
| KML_LEPTIS_POINTS | 52 داخل مجلد لبدة؛ الموقع الرئيسي Point إضافي |
| KML_LEPTIS_POLYGONS | 0 |
| GEOJSON_TOTAL | 207 |
| GEOJSON_LEPTIS_TOTAL | 53 |
| MAP_RENDERED_LEPTIS_TOTAL | 53 |
| LINKED_IMAGE_FEATURES | 4 |
| FEATURES_WITHOUT_IMAGES | 49 |
| REVIEW_REQUIRED_FEATURES (لبدة) | 1 |

كل Placemark من KML حُوّل دون إسقاط أو دمج. يوجد Placemark واحد خارج لبدة في KML بلا هندسة؛ حُفظ كـ `GeometryCollection` فارغ مع `review_status=review_required` بدل حذفه. لا توجد مضلعات في مجموعة لبدة المصدرية.

## المعرفات الأساسية

- الموقع الرئيسي: `WH-MAIN-001` — `موقع لبدة الأثري – لبدة الكبرى – لبتس ماغنا`، `site_role=primary`.
- قوس سبتيموس سفيروس: `WH-LY-001-0001`.
- المسرح الروماني: `WH-LY-001-0002`.
- استراحة تازويت: `WH-MAIN-001-C0004`.
- قوس ماركوس أوروليوس: `WH-MAIN-001-C0044`.

كل المعالم التابعة تستخدم `parent_site_id=WH-MAIN-001` وتحافظ على ترتيب KML والاسم والوصف والإحداثيات وExtendedData والمجلد المصدر.

## الصور والحقوق

- الصور المؤكدة المرتبطة: الموقع الرئيسي، قوس سبتيموس سفيروس، المسرح الروماني، والسوق الرومانية.
- صور المسرح والقوس مرتبطة بالـ Placemark الحقيقي، ولا يوجد fallback يعتمد على الاسم.
- الصور العامة فقط مرتبطة بالموقع الرئيسي؛ المعالم بلا صور تبقى ظاهرة وتستخدم placeholder خاصًا بها.
- صور `official` موسومة `official_center_media` و`institutional_ownership`، وصور `source` موسومة `existing_atlas_media` و`existing_project_asset`.
- سجل الربط الكامل: `docs/media-linkage/leptis-complete-image-linkage.csv` (240 صفًا، 78 مجموعة تكرار SHA-256). الصور الأصلية لم تُحذف أو تُعدّل.
- النسخ المنشورة منظمة تحت `assets/media/LIBYA/heritage/leptis-magna/published/`، والصور غير المؤكدة محفوظة في `review-required` وغير مرتبطة بالـ GeoJSON.

## واجهة الصور

`assets/app.js` يقرأ `local_images`, `images`, `photos`, `image`, `photo`, و`external_images` سواء كانت مصفوفة أو نصًا، يطبّق المسارات النسبية وGitHub Pages base path وURL encoding، ويزيل التكرارات. الـ popup يعرض الصورة الرئيسية، الصور المصغرة، السابق/التالي، العداد، الفتح بالحجم الكامل، lazy loading وplaceholder عند غياب الصور، مع عزل فشل صورة واحدة.

## نتائج الاختبار

- `KML_TO_GEOJSON_COUNT_MATCH = PASS`
- `ALL_LEPTIS_FEATURES_RENDERED = PASS`
- `MAIN_SITE_POPUP = PASS`
- `THEATRE_POPUP_IMAGE = PASS`
- `ARCH_POPUP_IMAGE = PASS`
- `OFFICIAL_IMAGES_HTTP = PASS` (HTTP 200 وContent-Type يبدأ بـ `image/`)
- `NO_IMAGE_404 = PASS`
- `NO_CONSOLE_ERRORS = PASS`
- `FAILED = 0`

تم اختبار البحث عن قوس سبتيموس سفيروس، إخفاء/إظهار مجموعة التراث، popup لمعالم ذات صور وبدون صور، وعدم وجود طلبات فاشلة. لم يُنفّذ commit أو push أو نشر.

## الملفات الجديدة/المعدلة

- `data/layers/world-heritage.geojson`
- `assets/app.js`
- `assets/styles.css`
- `docs/media-linkage/leptis-complete-image-linkage.csv`
- `scripts/validate-leptis-complete.mjs`
- هذا التقرير
- مجلدات النشر المنظمة للصور.

## استكمال الربط المحافظ

أضيفت صورة `Leptis-Magna-il-mercato-Homs-Al-Murqub-Libya-400x600.jpg` إلى `WH-LY-001-0048` بعد مطابقة اسم المعلم وسياقه، ولم تُستخدم صورة `السوق البونيقي.jpg` لأنها لا تثبت السوق الرومانية. لم تُربط صور المصارعة أو الصور العامة غير المؤكدة بالمدرج أو ميدان السباق؛ بقيت في `review-required`، كما بقي المتحف البونيقي والضريح البونيقي والميدان الفورم دون صورة مؤكدة.
