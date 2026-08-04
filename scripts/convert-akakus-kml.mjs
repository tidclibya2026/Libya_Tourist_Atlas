import fs from "node:fs";
import path from "node:path";

const root = process.cwd();

const inputPath = path.join(
  root,
  "data",
  "source-kml",
  "akakus.kml"
);

const outputPath = path.join(
  root,
  "data",
  "layers",
  "akakus.geojson"
);

const reportPath = path.join(
  root,
  "docs",
  "layers",
  "akakus",
  "akakus-layer-summary.json"
);

if (!fs.existsSync(inputPath)) {
  throw new Error(
    `KML source file not found: ${inputPath}`
  );
}

const xml = fs.readFileSync(
  inputPath,
  "utf8"
);

function decodeXml(value) {
  return String(value ?? "")
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&apos;", "'");
}

function stripCdata(value) {
  return String(value ?? "")
    .replace(/^<!\[CDATA\[/, "")
    .replace(/\]\]>$/, "");
}

function cleanText(value) {
  return decodeXml(
    stripCdata(value)
  )
    .replace(/[\u200E\u200F\u202A-\u202E]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function extractTag(block, tagName) {
  const expression = new RegExp(
    `<${tagName}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`,
    "i"
  );

  const match = block.match(expression);

  return match
    ? cleanText(match[1])
    : "";
}

function extractRawTag(block, tagName) {
  const expression = new RegExp(
    `<${tagName}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`,
    "i"
  );

  const match = block.match(expression);

  return match
    ? stripCdata(match[1]).trim()
    : "";
}

function extractImageUrls(descriptionHtml) {
  const urls = [];
  const expression =
    /<img[^>]+src=["']([^"']+)["']/gi;

  let match;

  while (
    (match = expression.exec(descriptionHtml))
  ) {
    urls.push(decodeXml(match[1]));
  }

  return [...new Set(urls)];
}

function htmlToText(html) {
  return cleanText(
    String(html ?? "")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<\/p>/gi, " ")
      .replace(/<[^>]+>/g, " ")
  );
}

function folderBlocks(kml) {
  const folders = [];
  const expression =
    /<Folder(?:\s[^>]*)?>([\s\S]*?)<\/Folder>/gi;

  let match;

  while ((match = expression.exec(kml))) {
    folders.push(match[1]);
  }

  return folders;
}

function placemarkBlocks(block) {
  const placemarks = [];
  const expression =
    /<Placemark(?:\s[^>]*)?>([\s\S]*?)<\/Placemark>/gi;

  let match;

  while ((match = expression.exec(block))) {
    placemarks.push(match[1]);
  }

  return placemarks;
}

function extractCoordinates(placemark) {
  const coordinateText =
    extractTag(placemark, "coordinates");

  if (!coordinateText) {
    return null;
  }

  const firstCoordinate =
    coordinateText
      .trim()
      .split(/\s+/)[0];

  const parts = firstCoordinate
    .split(",")
    .map(Number);

  if (
    parts.length < 2 ||
    !Number.isFinite(parts[0]) ||
    !Number.isFinite(parts[1])
  ) {
    return null;
  }

  return [
    parts[0],
    parts[1]
  ];
}

function normalizeCategory(folderName) {
  const normalized = String(folderName ?? "")
    .trim()
    .toLowerCase();

  const technicalFolders = new Set([
    "lyshp",
    "shp",
    "layer",
    "layers",
    "document"
  ]);

  if (technicalFolders.has(normalized)) {
    return null;
  }

  const categories = {
    "اقواس صخرية":
      "الأقواس الصخرية",

    "الأقواس الصخرية":
      "الأقواس الصخرية",

    "الوديان":
      "الوديان",

    "ابار":
      "الآبار",

    "آبار":
      "الآبار",

    "المداخل":
      "المداخل والمسارات",

    "الفن الصخري والتراث الثقافي":
      "الفن الصخري والتراث الثقافي",

    "تجمعات سكانية وخدمات":
      "التجمعات السكانية والخدمات",

    "التجمعات السكانية والخدمات":
      "التجمعات السكانية والخدمات",

    "الكهوف والملاجىء":
      "الكهوف والملاجئ",

    "الكهوف والملاجئ":
      "الكهوف والملاجئ"
  };

  return categories[normalized] ||
    folderName ||
    "غير مصنف";
}


const features = [];
const categoryCounts = {};
const invalidRows = [];

let sourceIndex = 0;

for (const folder of folderBlocks(xml)) {
  const folderName = extractTag(
    folder,
    "name"
  );

  const category =
    normalizeCategory(folderName);

  if (!category) {
    continue;
  }

  for (
    const placemark of
    placemarkBlocks(folder)
  ) {
    sourceIndex += 1;

    const coordinates =
      extractCoordinates(placemark);

    const name =
      extractTag(placemark, "name");

    if (!name) {
      invalidRows.push({
        source_index: sourceIndex,
        name: "",
        category,
        issue: "missing_name"
      });

      continue;
    }

    const rawDescription =
      extractRawTag(
        placemark,
        "description"
      );

    const description =
      htmlToText(rawDescription);

    const externalImages =
      extractImageUrls(rawDescription);

    if (!coordinates) {
      invalidRows.push({
        source_index: sourceIndex,
        name,
        category,
        issue:
          "missing_or_invalid_coordinates"
      });

      continue;
    }

    categoryCounts[category] =
      (categoryCounts[category] || 0) + 1;

    features.push({
      type: "Feature",

      id: `AKK-${String(sourceIndex).padStart(
        4,
        "0"
      )}`,

      geometry: {
        type: "Point",
        coordinates
      },

      properties: {
        id: `AKK-${String(sourceIndex).padStart(
          4,
          "0"
        )}`,

        name_ar: name,
        name_en: "",

        layer_id: "akakus",
        layer_name_ar:
          "أكاكوس – الفن الصخري والمعالم الطبيعية والثقافية",

        category_ar: category,
        source_folder: folderName,

        description_ar: description,

        external_images:
          externalImages,

        local_images: [],

        media_status:
          externalImages.length
            ? "external_reference_only"
            : "no_media",

        verification_status:
          "source_kml_imported",

        source_file:
          "data/source-kml/akakus.kml",

        source_index: sourceIndex,

        publication_status:
          "published"
      }
    });
  }
}

const geojson = {
  type: "FeatureCollection",

  name:
    "Akakus Rock Art and Natural Cultural Sites",

  metadata: {
    layer_id: "akakus",

    name_ar:
      "أكاكوس – الفن الصخري والمعالم الطبيعية والثقافية",

    name_en:
      "Akakus Rock Art, Natural and Cultural Sites",

    version: "1.0.0",

    source:
      "data/source-kml/akakus.kml",

    generated_at:
      new Date().toISOString(),

    total_features:
      features.length,

    geometry_type:
      "Point",

    coordinate_reference_system:
      "EPSG:4326"
  },

  features
};

fs.writeFileSync(
  outputPath,
  JSON.stringify(
    geojson,
    null,
    2
  ),
  "utf8"
);

const summary = {
  layer_id: "akakus",

  source_placemarks:
    sourceIndex,

  valid_features:
    features.length,

  invalid_features:
    invalidRows.length,

  category_counts:
    categoryCounts,

  external_image_references:
    features.reduce(
      (total, feature) =>
        total +
        feature.properties
          .external_images.length,
      0
    ),

  output_file:
    "data/layers/akakus.geojson",

  invalid_rows:
    invalidRows
};

fs.writeFileSync(
  reportPath,
  JSON.stringify(
    summary,
    null,
    2
  ),
  "utf8"
);

console.log("");
console.log("Akakus KML conversion completed.");
console.log(`Source placemarks: ${sourceIndex}`);
console.log(`Valid features: ${features.length}`);
console.log(`Invalid features: ${invalidRows.length}`);
console.log("");
console.table(categoryCounts);



