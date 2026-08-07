# تقرير مراجعة الصور الوطنية — الدفعة الأولى

## الملخص التنفيذي

الحالة: **BATCH_1_PREPARED_FOR_MANUAL_REVIEW**. جرى تجهيز 592 Feature و1256 مرشحًا في سبع قوائم للتراث العالمي وأكاكوس والفن الصخري والمدينة القديمة طرابلس. لم تُستورد قرارات بشرية؛ لذلك عدد المراجعات البصرية الفعلية والصور المعتمدة للنشر يساوي صفرًا.

## المنهجية والحقوق

استُخدمت IDs الفعلية من GeoJSON وKML، والروابط الحالية وFeature ID وأسماء المجلدات لترشيح الصور فقط. لم تُعامل الأسماء كإثبات بصري. لم يوجد دليل حقوق محلي صريح مرتبط بالمرشحات، فبقيت unknown/requires_review.

## المخرجات

أُنشئت 35 Contact Sheet بحد أقصى 40 بطاقة، وسجل علاقات parent/component، وقرارات Primary فارغة، وGallery ومشتقات فارغة. لا GeoJSON أو صورة أصلية تغيرت، ولا صورة Google نُزّلت.

## المخاطر والخطوة التالية

الخطران الأساسيان هما التشابه البصري بين المواقع الأثرية واستخدام مشاهد سياقية عامة كصور محددة. الخطوة التالية هي تشغيل أداة المراجعة، تصدير `batch-1-review-decisions.json` أو CSV، ثم استيرادها بالسكريبت والتحقق من الحقوق قبل أي نشر.

## Institutional approval import (2026-08-07)

Approved by م. أسامة فرج الخبولي, مدير عام مركز المعلومات والتوثيق السياحي. The approval is limited to Batch 1 and records institutional publication approval, not ownership. Approved public derivatives: 74; approved primary images: 74; ambiguous/unsupported candidates remain deferred. Status: BATCH_1_INSTITUTIONALLY_APPROVED_AND_PUBLISHED.
