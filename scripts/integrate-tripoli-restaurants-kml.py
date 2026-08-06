import csv, html, json, math, re, unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/incoming/tripoli-restaurants.kml"
OUTPUT = ROOT / "data/layers/tripoli-restaurants.geojson"
EXISTING_CANDIDATES = [
    ROOT / "data/layers/restaurants.geojson",
    ROOT / "data/layers/food-drink.geojson",
    OUTPUT,
]
NS = {"k": "http://www.opengis.net/kml/2.2"}
CONTROL = re.compile(r"[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]")
IMG_RE = re.compile(r"<img\b[^>]*?src=[\"']([^\"']+)", re.I)
TAG_RE = re.compile(r"<[^>]+>")
TODAY = date.today().isoformat()

def clean(value):
    value = CONTROL.sub("", unicodedata.normalize("NFC", value or "")).replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value).strip(" \t\r\n.-–—_|،؛")
    parts = value.split()
    compact = []
    for part in parts:
        if not compact or part.casefold() != compact[-1].casefold(): compact.append(part)
    return " ".join(compact)

def norm(value):
    value = clean(value).casefold().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"[^\w\u0600-\u06ff]+", "", value)

def fields(pm):
    out = {}
    for data in pm.findall(".//k:ExtendedData/k:Data", NS):
        key, value = clean(data.get("name", "")), clean(data.findtext("k:value", default="", namespaces=NS))
        if key and value: out[key] = value
    for item in pm.findall(".//k:ExtendedData//k:SimpleData", NS):
        key, value = clean(item.get("name", "")), clean(item.text or "")
        if key and value: out[key] = value
    return out

def first(data, *keys):
    lookup = {clean(k).casefold(): clean(v) for k, v in data.items()}
    for key in keys:
        if lookup.get(key.casefold()): return lookup[key.casefold()]
    return ""

def description_text(raw, data):
    explicit = first(data, "الوصف", "description")
    if explicit: return explicit
    raw = re.sub(r"<img\b[^>]*>", " ", raw or "", flags=re.I)
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    text = html.unescape(TAG_RE.sub(" ", raw))
    lines = []
    for line in text.splitlines():
        line = clean(line)
        if not line or re.match(r"^(?:الوصف|المدينة/العنوان|الخدمات المتوفرة|الهاتف|facebook|placepageUri|gx_media_links)\s*:\s*$", line, re.I): continue
        if re.search(r"https?://", line): continue
        lines.append(line)
    return "\n".join(dict.fromkeys(lines))

def parse_kml(path):
    tree = ET.parse(path)
    parent = {child: node for node in tree.iter() for child in node}
    records = []
    for index, pm in enumerate(tree.findall(".//k:Placemark", NS), 1):
        point = pm.find(".//k:Point/k:coordinates", NS); coords = None
        if point is not None and point.text:
            try:
                pieces = point.text.strip().split(","); coords = (float(pieces[0]), float(pieces[1]))
            except (ValueError, IndexError): pass
        folder, node = "", parent.get(pm)
        while node is not None:
            if node.tag.endswith("Folder"):
                folder = clean(node.findtext("k:name", default="", namespaces=NS)); break
            node = parent.get(node)
        raw = pm.findtext("k:description", default="", namespaces=NS); data = fields(pm)
        images = list(dict.fromkeys(html.unescape(url) for url in IMG_RE.findall(raw or "")))
        media = first(data, "gx_media_links")
        if media and media not in images: images.append(media)
        records.append({"index": index, "name": clean(pm.findtext("k:name", default="", namespaces=NS)), "raw": raw, "description": description_text(raw, data), "coords": coords, "style": clean(pm.findtext("k:styleUrl", default="", namespaces=NS)), "folder": folder, "extended": data, "geometry": "Point" if point is not None else "other", "images": images})
    return records

def haversine(a, b):
    if not a or not b: return 10**9
    lon1, lat1, lon2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    dlon, dlat = lon2-lon1, lat2-lat1
    return 6371000 * 2 * math.asin(math.sqrt(math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2))

def similarity(a, b):
    a, b = norm(a), norm(b)
    if not a or not b: return 0
    if a == b: return 1
    pairs = lambda s: {s[i:i+2] for i in range(max(1, len(s)-1))}
    x, y = pairs(a), pairs(b)
    return 2 * len(x & y) / max(1, len(x) + len(y))

def classify(name, description, services):
    text = f"{name} {description} {services}".casefold()
    rules = [
        ("food_court", "ساحة مطاعم", "Food court", ["ساحة مطاعم", "food court"]),
        ("seafood_restaurant", "مطعم أسماك ومأكولات بحرية", "Seafood restaurant", ["مأكولات بحرية", "ماكولات بحرية", "فواكه البحر", "أسماك", "اسماك", "روبيان"]),
        ("traditional_restaurant", "مطعم شعبي أو تقليدي", "Traditional restaurant", ["شعبي", "طرابلسية", "ليبية", "مبكبكة", "كسكسي", "بازين"]),
        ("fast_food", "وجبات سريعة", "Fast food", ["وجبات سريعة", "fast food", "برجر", "burger", "فرايد تشيكن", "شاورما", "بيتزا"]),
        ("bakery", "مخبز", "Bakery", ["مخبز", "مخبوزات", "bakery"]),
        ("dessert_shop", "حلويات", "Dessert shop", ["حلويات", "dessert", "sweets"]),
        ("cafe_restaurant", "مطعم ومقهى", "Cafe restaurant", ["مطعم وكاف", "مطعم ومقه", "cafe and restaurant", "cafe & restaurant"]),
        ("international_restaurant", "مطعم دولي", "International restaurant", ["تركي", "لبنان", "إيطالي", "ايطالي", "باكستان", "مغربي", "دمشقي", "international"]),
    ]
    for code, ar, en, terms in rules:
        if any(term in text for term in terms): return code, ar, en, 1.0
    if "مطعم" in text or "restaurant" in text: return "restaurant", "مطعم", "Restaurant", 1.0
    if "كافي" in text or "cafe" in text or "مقهى" in text: return "review_required", "تحتاج مراجعة", "Review required", .3
    if any(term in text for term in ["قريل", "جريل", "grill", "مشاوي", "طعام"]): return "restaurant_other", "منشأة طعام أخرى", "Other food establishment", .7
    return "review_required", "تحتاج مراجعة", "Review required", .3

def read_existing():
    for path in EXISTING_CANDIDATES:
        if not path.exists(): continue
        try:
            data = json.loads(path.read_text(encoding="utf-8")); return data.get("features", [])
        except Exception: continue
    return []

source = parse_kml(SOURCE)
existing = read_existing()
existing_records = []
for feature in existing:
    p, geometry = feature.get("properties", {}), feature.get("geometry") or {}
    coords = geometry.get("coordinates") if geometry.get("type") == "Point" else None
    existing_records.append({"id": p.get("id"), "name": p.get("name_ar") or p.get("name"), "coords": coords, "properties": p})

name_counts = Counter(norm(r["name"]) for r in source if r["name"])
coord_counts = Counter((round(r["coords"][0], 7), round(r["coords"][1], 7)) for r in source if r["coords"])
used_existing, used_ids, features, match_rows = set(), set(), [], []
serials = [int(m.group(1)) for r in existing_records if r["id"] and (m := re.fullmatch(r"LY-FNB-RES-TRI-(\d+)", str(r["id"])))]
serial = max(serials or [0])

for record in source:
    candidates = []
    for ei, old in enumerate(existing_records):
        if ei in used_existing or not old["id"]: continue
        dist, sim = haversine(record["coords"], old["coords"]), similarity(record["name"], old["name"])
        if sim == 1 and dist <= 30: candidates.append((0, dist, ei, "exact_match"))
        elif sim >= .86 and dist <= 100: candidates.append((1, dist, ei, "high_confidence_match"))
    if candidates:
        _, distance, ei, status = sorted(candidates)[0]; old = existing_records[ei]; used_existing.add(ei); restaurant_id = old["id"]
        local_images = [x for x in old["properties"].get("local_images", []) if isinstance(x, str) and (ROOT / x.lstrip("/")).exists()]
    else:
        serial += 1; restaurant_id = f"LY-FNB-RES-TRI-{serial:05d}"; status = "new_feature"; distance = None; local_images = []
    used_ids.add(restaurant_id)
    ext, coords = record["extended"], record["coords"]
    services = first(ext, "الخدمات المتوفرة", "services")
    code, sub_ar, sub_en, class_score = classify(record["name"], record["description"], services)
    valid = bool(coords and -180 <= coords[0] <= 180 and -90 <= coords[1] <= 90)
    in_tripoli = bool(valid and 12.7 <= coords[0] <= 13.6 and 32.5 <= coords[1] <= 33.1)
    address = first(ext, "المدينة/العنوان", "العنوان", "address")
    phone = first(ext, "الهاتف", "phone") or None
    website = first(ext, "website", "الموقع الإلكتروني") or None
    if website and not website.startswith(("http://", "https://")): website = None
    source_image = record["images"][0] if record["images"] else None
    provider = "google_mymaps" if source_image and ("googleusercontent" in source_image or "mymaps.usercontent.google.com" in source_image) else ("remote_other" if source_image else None)
    image_status = "temporary_source_reference" if source_image else "no_image"
    required = {"name": record["name"], "coordinates": in_tripoli, "classification": code != "review_required", "district": None, "address": address, "phone": phone, "website": website, "cuisine": None, "opening_hours": None, "license": None, "image": bool(local_images)}
    completeness = round(100 * sum(bool(v) for v in required.values()) / len(required))
    overall = round((1 + (1 if in_tripoli else 0) + class_score + (.5 if phone or website else 0) + (1 if local_images else (.3 if source_image else 0))) / 5, 2)
    quality = "verified" if completeness == 100 and in_tripoli else "high" if completeness >= 70 and in_tripoli else "medium" if completeness >= 45 and in_tripoli else "low" if in_tripoli else "review_required"
    props = {
        "id": restaurant_id, "name_ar": record["name"], "name_en": None, "name_normalized_ar": norm(record["name"]), "translation_status": "pending_review",
        "category": "الطعام والشراب", "subcategory_ar": sub_ar, "subcategory_en": sub_en, "facility_type_code": code,
        "municipality_ar": "طرابلس", "municipality_en": "Tripoli", "city_ar": "طرابلس", "city_en": "Tripoli", "district_ar": None, "district_en": None,
        "address_ar": address or None, "address_en": None, "longitude": coords[0] if coords else None, "latitude": coords[1] if coords else None,
        "source": "Tripoli restaurants team KML", "source_kml": "data/incoming/tripoli-restaurants.kml", "source_record_index": record["index"],
        "description_ar": record["description"] or None, "description_en": None, "phone": phone, "email": first(ext, "email", "البريد الإلكتروني") or None, "website": website,
        "cuisine_type_ar": None, "cuisine_type_en": None, "price_level": None, "opening_hours": None, "status": "active", "license_status": None,
        "data_quality_status": quality, "data_review_status": "review_required" if quality in ("low", "review_required") or code == "review_required" else "integrated",
        "source_image_url": source_image, "source_image_provider": provider, "source_image_status": image_status, "local_images": local_images, "image_count": len(local_images),
        "created_at": TODAY, "updated_at": TODAY, "name_score": 1 if record["name"] else 0, "coordinate_score": 1 if in_tripoli else 0,
        "classification_score": class_score, "contact_score": .5 if phone or website else 0, "image_score": 1 if local_images else (.3 if source_image else 0),
        "completeness_score": completeness / 100, "overall_quality_score": overall, "data_completeness_percent": completeness,
        "missing_fields": [key for key, value in required.items() if not value], "match_status": status,
        "coordinate_review_status": "valid" if in_tripoli else ("outside_tripoli_review_required" if valid else "invalid"), "coordinate_change_reason": None,
        "original_coordinates": list(coords) if coords else None,
    }
    features.append({"type": "Feature", "id": restaurant_id, "properties": props, "geometry": {"type": "Point", "coordinates": list(coords)} if valid else None})
    match_rows.append((record, props))

duplicate_rows = []
for i, a in enumerate(features):
    if not a["geometry"]: continue
    for b in features[i+1:]:
        if not b["geometry"]: continue
        pa, pb = a["properties"], b["properties"]
        distance = haversine(a["geometry"]["coordinates"], b["geometry"]["coordinates"]); sim = similarity(pa["name_ar"], pb["name_ar"])
        classification = ""
        if distance < 1 and sim >= .9: classification = "confirmed_duplicate"
        elif distance < 30 and sim == 1: classification = "confirmed_duplicate"
        elif distance < 100 and sim >= .8: classification = "review_required"
        if classification:
            duplicate_rows.append([pa["id"], pa["name_ar"], pb["id"], pb["name_ar"], round(distance, 1), round(sim, 3), classification, "retain_and_review", "No automatic merge performed"])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"type": "FeatureCollection", "name": "Tripoli restaurants", "metadata": {"source": "data/incoming/tripoli-restaurants.kml", "generated_at": TODAY, "feature_count": len(features)}, "features": features}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(header); writer.writerows(rows)

inventory = []
for record, props in match_rows:
    coords = record["coords"]
    inventory.append([record["index"], record["name"], norm(record["name"]), coords[0] if coords else "", coords[1] if coords else "", props["coordinate_review_status"], "available" if record["description"] else "missing", record["images"][0] if record["images"] else "", props["source_image_status"], record["style"], record["folder"], "duplicate_name" if name_counts[norm(record["name"])] > 1 else "unique", "duplicate_coordinate" if coords and coord_counts[(round(coords[0],7),round(coords[1],7))] > 1 else "unique", props["match_status"]])
write_csv(ROOT/"docs/layers/tripoli-restaurants-kml-inventory.csv", ["source_index","source_name","normalized_name","longitude","latitude","geometry_status","description_status","image_url","image_status","style_url","folder","duplicate_name_status","duplicate_coordinate_status","notes"], inventory)
write_csv(ROOT/"docs/layers/tripoli-restaurants-final-inventory.csv", ["id","name_ar","facility_type_code","district_ar","longitude","latitude","match_status","data_quality_status","completeness_percent","image_status"], [[p["id"],p["name_ar"],p["facility_type_code"],p["district_ar"] or "",p["longitude"],p["latitude"],p["match_status"],p["data_quality_status"],p["data_completeness_percent"],p["source_image_status"]] for p in (f["properties"] for f in features)])
write_csv(ROOT/"docs/review/tripoli-restaurants-duplicate-review.csv", ["record_a_id","record_a_name","record_b_id","record_b_name","distance_meters","name_similarity","duplicate_classification","recommended_action","notes"], duplicate_rows)
write_csv(ROOT/"docs/review/tripoli-restaurants-data-quality-review.csv", ["id","name_ar","quality_status","completeness_percent","missing_fields","review_status","notes"], [[p["id"],p["name_ar"],p["data_quality_status"],p["data_completeness_percent"],"|".join(p["missing_fields"]),p["data_review_status"],"Complete official fields; verify classification where flagged"] for p in (f["properties"] for f in features) if p["missing_fields"] or p["data_review_status"] == "review_required"])

types = Counter(f["properties"]["facility_type_code"] for f in features); qualities = Counter(f["properties"]["data_quality_status"] for f in features)
confirmed = sum(row[6] == "confirmed_duplicate" for row in duplicate_rows); review_dupes = sum(row[6] == "review_required" for row in duplicate_rows)
report = f"""# تقرير دمج طبقة مطاعم طرابلس

## الملخص

- نقاط المصدر: {len(source)}
- النقاط النهائية: {len(features)}
- المطابقات الحالية: {len(used_existing)}
- العناصر الجديدة: {len(features)-len(used_existing)}
- التكرارات المؤكدة للمراجعة: {confirmed}
- حالات التكرار التي تحتاج مراجعة: {review_dupes}
- حالات البيانات التي تحتاج مراجعة: {sum(f['properties']['data_review_status']=='review_required' for f in features)}

## توزيع التصنيفات

{chr(10).join(f'- {key}: {value}' for key,value in sorted(types.items()))}

## جودة البيانات

{chr(10).join(f'- {key}: {value}' for key,value in sorted(qualities.items()))}

## الفجوات

يلزم استكمال بيانات الأحياء والترخيص ونوع المطبخ والأسعار وساعات العمل والترجمات من الوزارة والجهات التابعة. حُفظت روابط صور Google وMy Maps كمراجع مصدر مؤقتة فقط، ولم تُنزّل أو تُعرض تلقائيًا. لم تُدمج حالات التكرار تلقائيًا.
"""
(ROOT/"docs/tripoli-restaurants-kml-integration-report.md").write_text(report, encoding="utf-8")

print(f"RESTAURANTS_SOURCE_KML_EXISTS = {SOURCE.exists()}")
print(f"RESTAURANTS_SOURCE_FILE_SIZE = {SOURCE.stat().st_size}")
print(f"RESTAURANTS_SOURCE_PLACEMARKS_TOTAL = {len(source)}")
print(f"RESTAURANTS_TOTAL_PLACEMARKS = {len(source)}")
print(f"RESTAURANTS_WITH_VALID_POINT_GEOMETRY = {sum(r['geometry']=='Point' and bool(r['coords']) for r in source)}")
print(f"RESTAURANTS_WITHOUT_COORDINATES = {sum(not r['coords'] for r in source)}")
print(f"RESTAURANTS_WITH_IMAGES = {sum(bool(r['images']) for r in source)}")
print(f"RESTAURANTS_WITHOUT_IMAGES = {sum(not r['images'] for r in source)}")
print(f"RESTAURANTS_WITH_DESCRIPTIONS = {sum(bool(r['description']) for r in source)}")
print(f"RESTAURANTS_WITHOUT_DESCRIPTIONS = {sum(not r['description'] for r in source)}")
print(f"RESTAURANTS_DUPLICATE_NAMES = {sum(v-1 for v in name_counts.values() if v>1)}")
print(f"RESTAURANTS_DUPLICATE_COORDINATES = {sum(v-1 for v in coord_counts.values() if v>1)}")
print(f"RESTAURANTS_INVALID_COORDINATES = {sum(not r['coords'] or not(-180<=r['coords'][0]<=180 and -90<=r['coords'][1]<=90) for r in source)}")
print(f"EXISTING_RESTAURANT_FEATURES = {len(existing_records)}")
print(f"MATCHED_EXISTING_RESTAURANTS = {len(used_existing)}")
print(f"NEW_RESTAURANT_FEATURES = {len(features)-len(used_existing)}")
print(f"PRESERVED_EXISTING_IDS = {len(used_existing)}")
print(f"DUPLICATE_IDS = {len(features)-len(used_ids)}")
print(f"VALID_RESTAURANT_COORDINATES = {sum(f['properties']['coordinate_review_status']=='valid' for f in features)}")
print(f"OUTSIDE_TRIPOLI_REVIEW_REQUIRED = {sum(f['properties']['coordinate_review_status']=='outside_tripoli_review_required' for f in features)}")
print("COORDINATES_SWAPPED = 0")
print("COORDINATES_CHANGED = 0")
print(f"RESTAURANTS_DUPLICATES_CONFIRMED = {confirmed}")
print(f"RESTAURANTS_DUPLICATES_REVIEW_REQUIRED = {review_dupes}")
for key in ["restaurant","fast_food","traditional_restaurant","seafood_restaurant","international_restaurant","cafe_restaurant","bakery","dessert_shop","food_court","restaurant_other","review_required"]: print(f"{key.upper()}_COUNT = {types[key]}")
