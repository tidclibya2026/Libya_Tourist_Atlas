# تكامل مدينة غدامس القديمة

- KML: `data/kml/world-heritage.kml`
- مجلد KML: `غدامس`
- الموقع الرئيسي: `WH-WORLD-C0004`
- `KML_GHADAMES_TOTAL = 29`
- `KML_GHADAMES_POINTS = 29`
- `KML_GHADAMES_POLYGONS = 0`
- `KML_GHADAMES_OTHER_GEOMETRIES = 0`
- `GEOJSON_GHADAMES_TOTAL = 29`

تم الحفاظ على المعرفات والهندسات والإحداثيات وترتيب العناصر. الموقع الرئيسي مضبوط على `مدينة غدامس القديمة` و`Old Town of Ghadames` و`site_role=primary`.

## الصور

- صور المصدر الرسمي: 38
- صور الأطلس السابقة: 0
- الصور الفريدة: 35
- مجموعات التكرار SHA-256: 3
- الصور المرتبطة: 5 مسارات على عنصرين
- الصور قيد المراجعة: 33 نسخة في `published/review-required`

تم ربط الصور العامة المؤكدة بالموقع الرئيسي، وصورة `عين الفرس` بالعنصر `WH-LY-005-C0004`. الصور الأخرى غير المؤكدة لم تُربط بأي معلم فرعي.

## الاختبارات

- `KML_TO_GEOJSON_GHADAMES_MATCH = PASS`
- `ALL_GHADAMES_FEATURES_RENDERED = PASS`
- `GHADAMES_MAIN_POPUP = PASS`
- `GHADAMES_AIN_AL_FARAS_POPUP = PASS`
- `GHADAMES_IMAGES_HTTP = PASS`
- `NO_IMAGE_404 = PASS`
- `NO_CONSOLE_ERRORS = PASS`
- `GHADAMES_COORDINATES_UNCHANGED = PASS`
- `FAILED = 0`

اختبار Playwright: `scripts/test-ghadames-complete-playwright.py`. اختبار البيانات: `scripts/validate-ghadames-complete.mjs`.
