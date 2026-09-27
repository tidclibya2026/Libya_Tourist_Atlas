from PIL import Image, ImageOps, ImageDraw, ImageFont
from pathlib import Path
import math

source = Path("public/hero")
files = sorted(
    p for p in source.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)

cols = 4
cell_w, cell_h = 400, 270
thumb_w, thumb_h = 380, 215
rows = math.ceil(len(files) / cols)

sheet = Image.new(
    "RGB",
    (cols * cell_w, rows * cell_h),
    "white"
)
draw = ImageDraw.Draw(sheet)

for i, path in enumerate(files):
    x = (i % cols) * cell_w
    y = (i // cols) * cell_h

    try:
        with Image.open(path) as original:
            image = ImageOps.contain(
                original.convert("RGB"),
                (thumb_w, thumb_h)
            )
            px = x + (cell_w - image.width) // 2
            py = y + 5
            sheet.paste(image, (px, py))

        label = f"{i + 1:02d} - {path.name}"
        if len(label) > 46:
            label = label[:43] + "..."

        draw.text(
            (x + 10, y + 225),
            label,
            fill="black"
        )
    except Exception as exc:
        draw.text(
            (x + 10, y + 20),
            f"ERROR: {path.name}",
            fill="red"
        )
        print(path.name, exc)

output = source / "hero-contact-sheet.jpg"
sheet.save(output, quality=88)

print(f"Images: {len(files)}")
print(f"Contact sheet: {output.resolve()}")
