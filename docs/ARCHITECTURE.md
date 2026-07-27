# معمارية نسخة العرض الثابتة — أطلس ليبيا السياحي

## القرار المعماري
هذه النسخة **واجهة عرض فقط** ولا تستبدل منصة `lsta.ly` الحكومية. لا تحتوي على Backend أو قاعدة بيانات أو تسجيل دخول أو مسار مراجعة واعتماد.

```text
KML محلي + GeoJSON من GitHub + صور داخل وصف KML
                    ↓
         Static Layer Configuration
                    ↓
 Leaflet + leaflet-omnivore + MarkerCluster
                    ↓
  واجهة عربية RTL / بحث / طبقات / بطاقات مواقع
                    ↓
 GitHub Pages أو أي Web Server ثابت
```

## المكونات
1. `index.html`: الهيكل العام للعرض.
2. `assets/styles.css`: الهوية البصرية والاستجابة للشاشات.
3. `assets/app.js`: تعريف الطبقات، التحميل الكسول، التصنيف، البحث، وعرض الصور.
4. `data/kml/`: ملفات KML الأصلية أو النسخ المستصلحة تقنيًا للعرض.
5. مصدر GitHub خارجي: `mapatlas.geojson` لطبقة الموارد الطبيعية.

## مبادئ التنفيذ
- تحميل الطبقات عند الطلب Lazy Loading.
- عدم تعديل بيانات المصدر أو مراجعتها ضمن نسخة العرض.
- الاستفادة من الصور الموجودة داخل KML.
- عزل نسخة العرض عن Staging والسجل الوطني ومنظومة الاعتماد.
- سهولة النشر على GitHub Pages دون خادم.

## العلاقة مع المنصة التشغيلية
منصة `lsta.ly` تظل المعمارية الحكومية الكاملة:
KML/KMZ/GeoJSON/Excel → Importer/Validation → Staging → Review → National Registry/PostGIS → FastAPI → Government Portal/GIS/Reports.
