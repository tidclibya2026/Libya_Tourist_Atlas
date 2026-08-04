from __future__ import annotations

import csv
import hashlib
import shutil
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
IMAGE_ROOT = ROOT / "assets" / "images"
KML_ROOT = ROOT / "data" / "kml" / "final"
REPORT_DIR = ROOT / "docs"
BACKUP_DIR = ROOT.parent / "Libya_Tourist_Atlas_media_backup"

MAX_DIMENSION = 1920
WEBP_QUALITY = 82
RASTER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
TEXT_EXTENSIONS = {".kml", ".xml", ".json", ".js", ".html"}

def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()

def backup(path: Path) -> None:
    target = BACKUP_DIR / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def convert(src: Path):
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if max(im.size) > MAX_DIMENSION:
                im.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            has_alpha = "A" in im.getbands()
            im = im.convert("RGBA" if has_alpha else "RGB")
            dst = src.with_suffix(".webp")
            tmp = dst.with_suffix(".webp.tmp")
            im.save(tmp, format="WEBP", quality=WEBP_QUALITY, method=6)
        if tmp.stat().st_size >= src.stat().st_size * 0.95:
            tmp.unlink(missing_ok=True)
            return None, "kept"
        backup(src)
        if dst.exists() and dst != src:
            backup(dst)
            dst.unlink()
        tmp.replace(dst)
        if dst != src:
            src.unlink()
        return dst, "converted"
    except Exception as exc:
        return None, f"error:{type(exc).__name__}:{exc}"

def update_references(mapping):
    files = []
    if KML_ROOT.exists():
        files.extend(p for p in KML_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS)
    for extra in [ROOT / "assets" / "app.js", ROOT / "assets" / "media-utils.js", ROOT / "index.html"]:
        if extra.exists():
            files.append(extra)
    changed = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        original = text
        replacements = 0
        for old, new in mapping.items():
            for variant in [old, "/" + old, old.replace("/", "\\"), "/" + old.replace("/", "\\")]:
                replacement = "/" + new if variant.startswith("/") else new
                count = text.count(variant)
                if count:
                    text = text.replace(variant, replacement)
                    replacements += count
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append((rel(path), replacements))
    return changed

def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in IMAGE_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in RASTER_EXTENSIONS)
    before = sum(p.stat().st_size for p in files)
    rows = []
    mapping = {}
    for i, src in enumerate(files, start=1):
        old_rel = rel(src)
        old_size = src.stat().st_size
        old_hash = sha256(src)
        dst, status = convert(src)
        if dst:
            new_rel = rel(dst)
            new_size = dst.stat().st_size
            new_hash = sha256(dst)
            mapping[old_rel] = new_rel
        else:
            new_rel = old_rel
            new_size = old_size
            new_hash = old_hash
        rows.append({
            "index": i, "status": status, "old_path": old_rel, "new_path": new_rel,
            "old_bytes": old_size, "new_bytes": new_size, "saved_bytes": old_size - new_size,
            "old_sha256": old_hash, "new_sha256": new_hash
        })
        print(f"[{i}/{len(files)}] {status}: {old_rel}")
    changed = update_references(mapping)
    current = [p for p in IMAGE_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in RASTER_EXTENSIONS]
    after = sum(p.stat().st_size for p in current)

    with (REPORT_DIR / "media-optimization-report.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    with (REPORT_DIR / "media-reference-update-report.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "replacement_count"])
        writer.writeheader()
        for file, count in changed:
            writer.writerow({"file": file, "replacement_count": count})

    (REPORT_DIR / "media-optimization-summary.md").write_text(
        f"# Media optimization summary\n\n"
        f"- Images scanned: {len(files):,}\n"
        f"- Before: {before / 1024 / 1024:.2f} MB\n"
        f"- After: {after / 1024 / 1024:.2f} MB\n"
        f"- Saved: {(before-after) / 1024 / 1024:.2f} MB\n"
        f"- Reduction: {((before-after)/before*100) if before else 0:.2f}%\n"
        f"- Backup: {BACKUP_DIR}\n",
        encoding="utf-8"
    )
    print(f"Before: {before / 1024 / 1024:.2f} MB")
    print(f"After: {after / 1024 / 1024:.2f} MB")
    print(f"Backup: {BACKUP_DIR}")

if __name__ == "__main__":
    main()
