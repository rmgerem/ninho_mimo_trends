"""Crops each perfume out of the two flyer photos, enhances it, and composes it onto
an elegant tinted card background matching the site's category colors.

Requires docs/perfumar_site/assets/flyer/masculino.jpg and feminino.jpg (the photos
the user provided). Writes <id>.jpg into both photo folders (perfumar_site and the
shared templates folder) -- real photos always win over the generated .svg fallback.

Run with: python crop_flyer_photos.py
"""
import os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
FLYER_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "perfumar_site", "assets", "flyer"))
DESTINATIONS = [
    os.path.join(HERE, "assets", "products"),
    os.path.normpath(os.path.join(HERE, "..", "..", "perfumar_site", "assets", "products")),
]

MASC_COLS = [(80, 212), (265, 400), (450, 585), (640, 775)]
MASC_ROW_BANDS = [(460, 565), (565, 645), (645, 720), (720, 798), (798, 898), (898, 1008), (1008, 1100)]
MASC_ROWS = [
    ["brz-urban", "bravus", "charmy", "brz-intense-men"],
    ["conquest", "champion", "brz-men", "elegante-sport"],
    ["personalz", "noble", "blue", "selvagem"],
    ["sweet-class", "silver-z", "code-man", "ahazzo"],
    ["boss-man", "mb-endless", "jump", "lord"],
    ["strong", "black-horse", "lord-green", "animalz"],
    ["loyal", "brz-dark", "tauren", "valien"],
]
ARABE_ROW_BANDS = [(1193, 1283), (1283, 1365)]
ARABE_ROWS = [
    ["golden-arabian", "rubi", "dunes", "sunshine"],
    ["malirah", "najad", "sharif", "zayan"],
]

FEM_COLS = [(80, 215), (280, 415), (475, 610), (660, 792)]
FEM_ROW_BANDS = [(420, 518), (518, 600), (600, 695), (695, 793), (793, 888), (888, 985), (985, 1075)]
FEM_ROWS = [
    ["brz-blossom", "brz-intense-woman", "luminous-flowers", "creta"],
    ["luminous-girl", "gold-woman", "brz-woman", "lys"],
    ["miss", "love-it", "la-vie-est-amour", "2-love"],
    ["beauty", "tuberose-shine", "autentica", "glow"],
    ["cintilante", "magic", "gs", "revolution"],
    ["tresor", "sweet-blue", "sweet", "unique"],
    ["five-z", "honey", "aura-rose", "isis"],
]

SPECIAL_BOXES = {
    "primavera": ("feminino", (340, 1178, 565, 1250)),
    "verao": ("feminino", (900, 1178, 1075, 1250)),
    "outono": ("feminino", (340, 1250, 565, 1330)),
    "inverno": ("feminino", (900, 1250, 1075, 1330)),
    "yria": ("feminino", (458, 1155, 555, 1275)),
    "darion": ("feminino", (650, 1155, 748, 1275)),
}

GENDER_BY_ID = {}
BOXES = {}  # id -> (source, box)

for rows, bands, cols in ((MASC_ROWS, MASC_ROW_BANDS, MASC_COLS), (ARABE_ROWS, ARABE_ROW_BANDS, MASC_COLS)):
    for row, (top, bottom) in zip(rows, bands):
        for pid, (left, right) in zip(row, cols):
            BOXES[pid] = ("masculino", (left, top, right, bottom))

for row, (top, bottom) in zip(FEM_ROWS, FEM_ROW_BANDS):
    for pid, (left, right) in zip(row, FEM_COLS):
        BOXES[pid] = ("feminino", (left, top, right, bottom))

BOXES.update(SPECIAL_BOXES)

MASC_IDS = {pid for row in MASC_ROWS for pid in row}
ARABE_IDS = {pid for row in ARABE_ROWS for pid in row}
FEM_IDS = {pid for row in FEM_ROWS for pid in row}
ESPECIAL_IDS = {"primavera", "verao", "outono", "inverno", "yria", "darion"}

for pid in MASC_IDS:
    GENDER_BY_ID[pid] = "masculino"
for pid in ARABE_IDS:
    GENDER_BY_ID[pid] = "arabe"
for pid in FEM_IDS:
    GENDER_BY_ID[pid] = "feminino"
for pid in ESPECIAL_IDS:
    GENDER_BY_ID[pid] = "especial"

BG_TINTS = {
    "masculino": ("#e7e5e1", "#c7d2cb"),
    "feminino": ("#fdf3ef", "#f6dcd4"),
    "arabe": ("#fbf1dc", "#f0dba8"),
    "especial": ("#f1eef7", "#dcd0ea"),
}

CANVAS_SIZE = (620, 620)
PADDING_FRAC = 0.06  # margin kept empty around the enhanced photo


def enhance(photo: Image.Image) -> Image.Image:
    photo = ImageOps.autocontrast(photo, cutoff=1)
    photo = ImageEnhance.Color(photo).enhance(1.12)
    photo = ImageEnhance.Contrast(photo).enhance(1.08)
    photo = ImageEnhance.Sharpness(photo).enhance(1.6)
    photo = photo.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    return photo


def radial_bg(size, top_color, bottom_color):
    bg = Image.new("RGB", size, top_color)
    draw = ImageDraw.Draw(bg)
    cx, cy = size[0] / 2, size[1] * 0.35
    max_r = (size[0] ** 2 + size[1] ** 2) ** 0.5 / 2
    steps = 60
    for i in range(steps, 0, -1):
        t = i / steps
        r = max_r * t
        color = tuple(int(top_color[c] + (bottom_color[c] - top_color[c]) * (1 - t)) for c in range(3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return bg.filter(ImageFilter.GaussianBlur(40))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def build_card(pid: str) -> Image.Image:
    source, box = BOXES[pid]
    src_img = Image.open(f"{FLYER_DIR}\\{source}.jpg").convert("RGB")
    photo = src_img.crop(box)
    photo = enhance(photo)

    gender = GENDER_BY_ID[pid]
    top_color, bottom_color = (hex_to_rgb(c) for c in BG_TINTS[gender])
    canvas = radial_bg(CANVAS_SIZE, top_color, bottom_color)

    max_w = int(CANVAS_SIZE[0] * (1 - 2 * PADDING_FRAC))
    max_h = int(CANVAS_SIZE[1] * (1 - 2 * PADDING_FRAC))
    scale = min(max_w / photo.width, max_h / photo.height)
    new_size = (max(1, int(photo.width * scale)), max(1, int(photo.height * scale)))
    photo = photo.resize(new_size, Image.LANCZOS)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    sx = (canvas.width - new_size[0]) // 2
    sy = (canvas.height - new_size[1]) // 2 + 10
    shadow_draw.rounded_rectangle(
        [sx + 6, sy + 10, sx + new_size[0] + 6, sy + new_size[1] + 10],
        radius=18, fill=(20, 15, 10, 70),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)

    card = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    mask = Image.new("L", new_size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, new_size[0], new_size[1]], radius=16, fill=255)
    card.paste(photo, ((canvas.width - new_size[0]) // 2, (canvas.height - new_size[1]) // 2), mask)

    result = Image.alpha_composite(canvas, card).convert("RGB")
    return result


def main():
    for dest in DESTINATIONS:
        os.makedirs(dest, exist_ok=True)

    ok, failed = 0, []
    for pid in BOXES:
        try:
            card = build_card(pid)
        except Exception as exc:  # noqa: BLE001
            failed.append((pid, str(exc)))
            continue
        for dest in DESTINATIONS:
            card.save(os.path.join(dest, f"{pid}.jpg"), quality=90)
        ok += 1

    print(f"Generated {ok} product photos into {len(DESTINATIONS)} folders.")
    if failed:
        print("Failed:", failed)


if __name__ == "__main__":
    main()
