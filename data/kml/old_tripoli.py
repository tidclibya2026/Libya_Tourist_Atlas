from __future__ import annotations

import csv
import hashlib
import mimetypes
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_KML = PROJECT_ROOT / "data" / "kml" / "old-tripoli.kml"
OUTPUT_KML = PROJECT_ROOT / "data" / "kml" / "old-tripoli-local-images.kml"
IMAGE_DIR = PROJECT_ROOT / "assets" / "images" / "old-tripoli"
REPORT_CSV = PROJECT_ROOT / "docs" / "old-tripoli-images-report.csv"

REQUEST_TIMEOUT = 45
MAX_RETRIES = 3
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/150 Safari/537.36"
)

IMG_SRC_PATTERN = re.compile(
    r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)(\2)',
    re.IGNORECASE | re.DOTALL,
)


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^\w\-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80] or "image"


def extension_from_response(url: str, response: requests.Response) -> str:
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()

    extension = mimetypes.guess_extension(content_type) if content_type else None
    if extension == ".jpe":
        extension = ".jpg"

    if extension in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
        return ".jpg" if extension == ".jpeg" else extension

    path_extension = Path(urlparse(url).path).suffix.lower()
    if path_extension in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}:
        return ".jpg" if path_extension == ".jpeg" else path_extension

    return ".jpg"


def download_image(
    session: requests.Session,
    url: str,
    index: int,
) -> tuple[bool, str, str]:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    domain = sanitize_filename(urlparse(url).netloc.split(".")[0])
    base_name = f"old-tripoli-{index:03d}-{domain}-{digest}"

    last_error = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Referer": "https://www.google.com/",
                },
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "image/" not in content_type and len(response.content) < 1024:
                raise ValueError(
                    f"الاستجابة ليست صورة صالحة: {content_type or 'unknown'}"
                )

            extension = extension_from_response(url, response)
            filename = f"{base_name}{extension}"
            output_file = IMAGE_DIR / filename
            output_file.write_bytes(response.content)

            relative_path = f"assets/images/old-tripoli/{filename}"
            return True, relative_path, ""

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 2)

    return False, "", last_error


def main() -> int:
    if not SOURCE_KML.exists():
        print(f"خطأ: لم يتم العثور على الملف:\n{SOURCE_KML}")
        return 1

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)

    kml_text = SOURCE_KML.read_text(encoding="utf-8", errors="replace")

    urls: list[str] = []
    for match in IMG_SRC_PATTERN.finditer(kml_text):
        url = match.group(3).strip()
        if url.startswith(("http://", "https://")) and url not in urls:
            urls.append(url)

    print(f"تم العثور على {len(urls)} رابط صورة خارجي.")

    session = requests.Session()
    replacements: dict[str, str] = {}
    report_rows: list[dict[str, str]] = []

    for index, url in enumerate(urls, start=1):
        print(f"[{index}/{len(urls)}] تنزيل الصورة...")
        success, local_path, error = download_image(session, url, index)

        if success:
            replacements[url] = local_path
            print(f"  تم: {local_path}")
            status = "downloaded"
        else:
            print(f"  فشل: {error}")
            status = "failed"

        report_rows.append(
            {
                "index": str(index),
                "status": status,
                "original_url": url,
                "local_path": local_path,
                "error": error,
            }
        )

    def replace_img_src(match: re.Match[str]) -> str:
        prefix, quote, url, closing_quote = match.groups()
        replacement = replacements.get(url.strip(), url)
        return f"{prefix}{quote}{replacement}{closing_quote}"

    updated_kml = IMG_SRC_PATTERN.sub(replace_img_src, kml_text)
    OUTPUT_KML.write_text(updated_kml, encoding="utf-8")

    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "status",
                "original_url",
                "local_path",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerows(report_rows)

    downloaded = sum(row["status"] == "downloaded" for row in report_rows)
    failed = len(report_rows) - downloaded

    print("\nاكتملت العملية.")
    print(f"الصور الناجحة: {downloaded}")
    print(f"الصور الفاشلة: {failed}")
    print(f"KML الجديد: {OUTPUT_KML}")
    print(f"تقرير النتائج: {REPORT_CSV}")

    if downloaded:
        print(
            "\nبعد المراجعة، استبدل old-tripoli.kml بالنسخة "
            "old-tripoli-local-images.kml أو عدّل app.js ليقرأ النسخة الجديدة."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
