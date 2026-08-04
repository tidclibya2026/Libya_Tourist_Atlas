import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

const filePath = path.join(
  root,
  "data",
  "layers",
  "akakus.geojson"
);

const data = JSON.parse(
  fs.readFileSync(filePath, "utf8")
);

const genericNames = new Set([
  "موقع فن صخري",
  "قوس صخري"
]);

const genericCounters = new Map();

for (const feature of data.features || []) {
  const properties = feature.properties || {};
  const sourceName = String(
    properties.name_ar || ""
  ).trim();

  properties.source_name_ar = sourceName;

  /*
   * الأسماء العامة صحيحة، لكنها تحتاج
   * رقمًا للتمييز في العرض والبحث.
   */
  if (genericNames.has(sourceName)) {
    const nextNumber =
      (genericCounters.get(sourceName) || 0) + 1;

    genericCounters.set(
      sourceName,
      nextNumber
    );

    properties.display_name_ar =
      `${sourceName} ${String(nextNumber).padStart(2, "0")}`;

    properties.naming_status =
      "generic_source_name";

    properties.naming_note_ar =
      "الموقع لا يحمل اسمًا محليًا موثقًا في المصدر، ولذلك يحتفظ الأطلس بالاسم العام مع رقم تعريفي للتمييز بين المواقع.";
  } else {
    properties.display_name_ar =
      sourceName;

    properties.naming_status =
      sourceName
        ? "source_name_available"
        : "missing_name";
  }

  /*
   * المقبرة الجرمنتية جزء من المسار السياحي،
   * وليست نقطة خارجة يجب حذفها.
   */
  if (
    sourceName.includes("مقبرة جرمنتية")
  ) {
    properties.category_ar =
      "الفن الصخري والتراث الثقافي";

    properties.subcategory_ar =
      "مواقع أثرية ومعمارية";

    properties.tourism_role =
      "tour_route_stop";

    properties.tourism_role_ar =
      "مزار أثري ضمن خط السير السياحي";

    properties.route_context_ar =
      "تُدرج المقبرة الجرمنتية ضمن المزارات المرتبطة بخطوط السير السياحية في نطاق غات وأكاكوس.";

    properties.spatial_scope =
      "extended_tourism_route";

    properties.verification_status =
      "source_kml_imported_owner_confirmed";
  }

  feature.properties = properties;
}

data.metadata ||= {};

data.metadata.naming_policy_ar =
  "تُحفظ الأسماء الأصلية الواردة في المصدر. المواقع التي تحمل أسماء عامة مثل موقع فن صخري أو قوس صخري تُميز بأرقام متسلسلة دون اختلاق أسماء جديدة.";

data.metadata.spatial_scope_ar =
  "تشمل الطبقة مواقع أكاكوس والمعالم والمزارات المرتبطة بخطوط السير السياحية في نطاق غات وأكاكوس.";

fs.writeFileSync(
  filePath,
  JSON.stringify(data, null, 2),
  "utf8"
);

console.log("");
console.log("Akakus tourism annotations completed.");
console.log(`Features: ${data.features.length}`);
console.log(
  "Generic rock-art sites:",
  genericCounters.get("موقع فن صخري") || 0
);
console.log(
  "Generic rock arches:",
  genericCounters.get("قوس صخري") || 0
);
