"""One-off calibration helper: fine grid overlay (every 10px) over a cropped region."""
from PIL import Image, ImageDraw

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"


def fine_grid(src, box, out_name, scale=2):
    img = Image.open(src).convert("RGB").crop(box)
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    ox, oy = box[0], box[1]
    for y in range(0, img.height, 10 * scale):
        orig_y = oy + y // scale
        color = (255, 0, 0) if orig_y % 50 == 0 else (0, 200, 255)
        draw.line([(0, y), (img.width, y)], fill=color, width=1)
        if orig_y % 50 == 0:
            draw.text((2, y + 1), str(orig_y), fill=(255, 0, 0))
    for x in range(0, img.width, 10 * scale):
        orig_x = ox + x // scale
        color = (255, 0, 0) if orig_x % 50 == 0 else (0, 200, 255)
        draw.line([(x, 0), (x, img.height)], fill=color, width=1)
        if orig_x % 50 == 0:
            draw.text((x + 1, 1), str(orig_x), fill=(255, 0, 0))
    img.save(f"{OUT_DIR}\\{out_name}.png")


# Masculino: first two rows (row bounds + columns) at higher res for precision.
fine_grid(f"{FLYER_DIR}\\masculino.jpg", (80, 440, 820, 680), "fine_masc_rows12")
fine_grid(f"{FLYER_DIR}\\masculino.jpg", (80, 1080, 820, 1390), "fine_masc_arabe")
print("done")
