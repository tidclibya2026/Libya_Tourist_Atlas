# تشخيص عدم ظهور صور الـ popup

## السبب الجذري

1. ملفات KML النهائية تخزن الصور غالبًا في `ExtendedData/Data[name="images_json"]/value`. طبقات أكاكوس وطرابلس القديمة والفنادق والاستثمار لا تحتوي غالبية نقاطها المصورة على عنصر `img` داخل `description`.
2. الدالة السابقة `extractPhotoPaths` لم تُدخل `images_json` أو `gx_media_links` أو `media` أو `source_media_url` ضمن مصادرها، ولذلك لم تصل هذه الصور إلى المعرض.
3. `cleanPopup` كان يستبدل `description` بمحتوى popup السابق الذي أنشأه Leaflet Omnivore. هذا المحتوى ملخص للخصائص ولا يضمن الاحتفاظ بعناصر الصور أو JSON الأصلي.
4. Omnivore يحول KML إلى GeoJSON ويفقد بعض تفاصيل `ExtendedData/SchemaData`. الإصلاح يقرأ KML كنص، يحتفظ بعناصر `Placemark` الأصلية، ثم يطابقها بالترتيب مع طبقات Leaflet.

## العينات المفحوصة

فُحصت أول 10 نقاط ذات حقول وسائط من كل من: أكاكوس، المدينة القديمة طرابلس، الفنادق، التراث العالمي، المنتجعات، والاستثمار. جميع العينات الستين احتوت `images_json`؛ عناصر `img` ظهرت في عينات التراث العالمي والمنتجعات فقط، بينما اعتمدت الطبقات الأخرى على `ExtendedData`.

## قبل الإصلاح وبعده

- قبل: `cleanPopup(layer, cfg)` يقرأ خصائص GeoJSON الجزئية ثم يبحث فقط في `photo/photos/image/images/popupinfo`.
- بعد: `cleanPopup(layer, cfg, placemark, kmlFileUrl)` يستدعي `extractPlacemarkProperties` و`extractPlacemarkImages` على عنصر Placemark الأصلي، ويقرأ `Data/value` و`SimpleData` وكل حقول الوسائط المطلوبة.

مثال مسار خام: `/assets/images/world-heritage/world-heritage-001.png`.

على GitHub Pages يحل إلى: `https://tidclibya2026.github.io/Libya_Tourist_Atlas/assets/images/world-heritage/world-heritage-001.png`، وليس إلى جذر النطاق.
