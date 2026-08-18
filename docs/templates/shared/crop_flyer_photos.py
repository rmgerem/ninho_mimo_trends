"""Crops each perfume out of the two flyer photos, enhances it, and composes it onto
an elegant tinted card background matching the site's category colors.

Requires docs/perfumar_site/assets/flyer/masculino.jpg and feminino.jpg (the photos
the user provided). Writes <id>.jpg into both photo folders (perfumar_site and the
shared templates folder) -- real photos always win over the generated .svg fallback.

Run with: python crop_flyer_photos.py
"""
import os
import subprocess
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
FLYER_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "perfumar_site", "assets", "flyer"))
PDF_PATH = os.path.expanduser("~/Downloads/Catálogo AGOSTO-2026 LADO A LADO.pdf")
PDF_RENDER_DIR = "/tmp/perfumar_pdf_hi_240"
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
    "primavera": ("feminino", (108, 1195, 170, 1260)),
    "verao": ("feminino", (300, 1195, 360, 1260)),
    "outono": ("feminino", (108, 1288, 170, 1348)),
    "inverno": ("feminino", (300, 1288, 360, 1348)),
    "yria": ("feminino", (450, 1192, 538, 1256)),
    "darion": ("feminino", (585, 1192, 670, 1256)),
}

GENDER_BY_ID = {}
BOXES = {}  # id -> (source, box)

for rows, bands, cols in ((MASC_ROWS, MASC_ROW_BANDS, MASC_COLS), (ARABE_ROWS, ARABE_ROW_BANDS, MASC_COLS)):
    for row, (top, bottom) in zip(rows, bands):
        for pid, (left, right) in zip(row, cols):
            BOXES[pid] = ("masculino", (left, top + 36, right - 45, bottom - 5))

for row, (top, bottom) in zip(FEM_ROWS, FEM_ROW_BANDS):
    for pid, (left, right) in zip(row, FEM_COLS):
        BOXES[pid] = ("feminino", (left, top + 36, right - 44, bottom - 5))

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
EDITORIAL_SIZE = (900, 620)

# Product hero crops from the high-resolution digital catalog render.
# Coordinates are for pdftoppm rendered at 240 DPI (3308 x 2315 px).
EDITORIAL_BOXES = {
    # Femininos
    "brz-blossom": (12, (170, 260, 880, 1120)),
    "glow": (12, (930, 120, 1645, 1000)),
    "miss": (12, (170, 1130, 880, 2190)),
    "luminous-flowers": (12, (930, 1070, 1645, 2150)),
    "love-it": (13, (170, 850, 1260, 2240)),
    "lys": (13, (1760, 270, 3270, 1080)),
    "tuberose-shine": (13, (1690, 1180, 3270, 2220)),
    "sweet": (14, (170, 160, 1120, 760)),
    "gs": (14, (170, 640, 1120, 1230)),
    "magic": (14, (170, 1200, 1120, 2180)),
    "sweet-blue": (14, (1660, 0, 3270, 1270)),
    "creta": (15, (170, 220, 920, 970)),
    "isis": (15, (170, 1110, 920, 2050)),
    "honey": (15, (1040, 650, 2000, 1760)),
    "revolution": (16, (170, 600, 1700, 1800)),
    "2-love": (16, (2150, 100, 3270, 1000)),
    "brz-intense-woman": (16, (2380, 1120, 3270, 1980)),
    "luminous-girl": (17, (170, 120, 1200, 940)),
    "gold-woman": (17, (1640, 120, 2450, 900)),
    "tresor": (17, (170, 1160, 1100, 2200)),
    "autentica": (17, (2320, 1150, 3270, 2150)),
    "brz-woman": (18, (170, 410, 1150, 1320)),
    # Masculinos
    "ahazzo": (18, (2500, 220, 3270, 940)),
    "tauren": (18, (2480, 840, 3270, 1490)),
    "brz-men": (18, (930, 1330, 1660, 2180)),
    "lord-green": (18, (2440, 1460, 3270, 2180)),
    "silver-z": (19, (170, 300, 1160, 1650)),
    "sweet-class": (19, (1460, 310, 2310, 1160)),
    "brz-dark": (19, (1870, 240, 2700, 1010)),
    "bravus": (19, (2350, 420, 3270, 1180)),
    "charmy": (20, (170, 140, 1640, 1040)),
    "code-man": (20, (170, 1080, 900, 2240)),
    "brz-urban": (20, (910, 1080, 1640, 2240)),
    "animalz": (20, (1665, 910, 2200, 1990)),
    "loyal": (20, (2210, 900, 2760, 1980)),
    "lord": (20, (2760, 640, 3270, 2060)),
    "conquest": (21, (170, 470, 920, 1630)),
    "boss-man": (21, (2260, 240, 3270, 900)),
    "noble": (21, (1450, 690, 2440, 1440)),
    "brz-intense-men": (21, (2350, 1390, 3270, 2140)),
    "selvagem": (22, (170, 210, 1610, 1050)),
    "blue": (22, (170, 1080, 1180, 2150)),
    "valien": (22, (1510, 1040, 2920, 2180)),
    "elegante-sport": (23, (170, 120, 1630, 980)),
    "jump": (23, (170, 1030, 1630, 2220)),
    "champion": (23, (1650, 120, 3270, 1380)),
    # Árabes
    "rubi": (8, (1320, 670, 2080, 1310)),
    "sunshine": (8, (2130, 160, 3030, 910)),
    "zayan": (8, (1360, 1360, 2240, 2020)),
    "sharif": (9, (930, 80, 2170, 700)),
    "dunes": (9, (190, 560, 980, 1300)),
    "golden-arabian": (9, (700, 1130, 1440, 1980)),
    "malirah": (9, (2200, 120, 3270, 910)),
    "najad": (9, (2140, 1110, 3270, 1990)),
    # Especiais
    "primavera": (11, (170, 80, 1645, 840)),
    "verao": (11, (1665, 80, 3270, 840)),
    "outono": (11, (170, 900, 1645, 1680)),
    "inverno": (11, (1665, 900, 3270, 1680)),
    "yria": (10, (170, 850, 690, 1690)),
}


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


def render_pdf_pages():
    page = os.path.join(PDF_RENDER_DIR, "page-12.jpg")
    if os.path.exists(page) or not os.path.exists(PDF_PATH):
        return
    os.makedirs(PDF_RENDER_DIR, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-f", "8", "-l", "23", "-r", "240", "-jpeg", PDF_PATH, os.path.join(PDF_RENDER_DIR, "page")],
        check=True,
    )


def pdf_page_path(page: int) -> str:
    with_zero = os.path.join(PDF_RENDER_DIR, f"page-{page:02d}.jpg")
    without_zero = os.path.join(PDF_RENDER_DIR, f"page-{page}.jpg")
    return with_zero if os.path.exists(with_zero) else without_zero


def cover_resize(photo: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / photo.width, size[1] / photo.height)
    resized = photo.resize((int(photo.width * scale), int(photo.height * scale)), Image.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def build_editorial_card(pid: str) -> Image.Image | None:
    if pid not in EDITORIAL_BOXES:
        return None
    page_num, box = EDITORIAL_BOXES[pid]
    page = pdf_page_path(page_num)
    if not os.path.exists(page):
        return None
    photo = Image.open(page).convert("RGB").crop(box)
    photo = ImageOps.autocontrast(photo, cutoff=0.5)
    photo = ImageEnhance.Color(photo).enhance(1.04)
    photo = ImageEnhance.Sharpness(photo).enhance(1.08)
    return cover_resize(photo, EDITORIAL_SIZE)


def build_flyer_card(pid: str) -> Image.Image:
    source, box = BOXES[pid]
    src_img = Image.open(os.path.join(FLYER_DIR, f"{source}.jpg")).convert("RGB")
    photo = src_img.crop(box)
    photo = enhance(photo)

    gender = GENDER_BY_ID[pid]
    top_color, bottom_color = (hex_to_rgb(c) for c in BG_TINTS[gender])
    canvas = radial_bg(CANVAS_SIZE, top_color, bottom_color)

    max_w = int(CANVAS_SIZE[0] * 0.68)
    max_h = int(CANVAS_SIZE[1] * 0.48)
    scale = min(max_w / photo.width, max_h / photo.height)
    new_size = (max(1, int(photo.width * scale)), max(1, int(photo.height * scale)))
    photo = photo.resize(new_size, Image.LANCZOS)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    sx = (canvas.width - new_size[0]) // 2
    sy = (canvas.height - new_size[1]) // 2 + 18
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

    return Image.alpha_composite(canvas, card).convert("RGB").resize(EDITORIAL_SIZE, Image.LANCZOS)


def build_card(pid: str) -> Image.Image:
    return build_editorial_card(pid) or build_flyer_card(pid)


def main():
    render_pdf_pages()
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
