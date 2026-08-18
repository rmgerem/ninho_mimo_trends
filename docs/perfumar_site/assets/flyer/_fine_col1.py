"""One-off calibration: fine y-grid over column 1 strip across full height to find row boundaries."""
from PIL import Image, ImageDraw

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"


def fine_grid(src, box, out_name, scale=2, step=10, label_step=25):
    img = Image.open(src).convert("RGB").crop(box)
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    ox, oy = box[0], box[1]
    for y in range(0, img.height, step * scale):
        orig_y = oy + y // scale
        color = (255, 0, 0) if orig_y % label_step == 0 else (0, 200, 255)
        draw.line([(0, y), (img.width, y)], fill=color, width=1)
        if orig_y % label_step == 0:
            draw.text((2, y + 1), str(orig_y), fill=(255, 0, 0))
    img.save(f"{OUT_DIR}\\{out_name}.png")


fine_grid(f"{FLYER_DIR}\\masculino.jpg", (60, 440, 260, 1090), "fine_col1_rows_masc", scale=2, step=5, label_step=25)
fine_grid(f"{FLYER_DIR}\\masculino.jpg", (60, 1090, 260, 1400), "fine_col1_rows_arabe", scale=2, step=5, label_step=25)
print("done")
