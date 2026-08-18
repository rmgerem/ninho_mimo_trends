"""One-off calibration: overview grid + fine row/col grids for feminino.jpg."""
from PIL import Image, ImageDraw

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"


def fine_grid(src, box, out_name, scale=2, step=10, label_step=25, label_x=True, label_y=True):
    img = Image.open(src).convert("RGB").crop(box)
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    ox, oy = box[0], box[1]
    for y in range(0, img.height, step * scale):
        orig_y = oy + y // scale
        color = (255, 0, 0) if orig_y % label_step == 0 else (0, 200, 255)
        draw.line([(0, y), (img.width, y)], fill=color, width=1)
        if label_y and orig_y % label_step == 0:
            draw.text((2, y + 1), str(orig_y), fill=(255, 0, 0))
    for x in range(0, img.width, step * scale):
        orig_x = ox + x // scale
        color = (255, 0, 0) if orig_x % label_step == 0 else (0, 200, 255)
        draw.line([(x, 0), (x, img.height)], fill=color, width=1)
        if label_x and orig_x % label_step == 0:
            draw.text((x + 1, 1), str(orig_x), fill=(255, 0, 0))
    img.save(f"{OUT_DIR}\\{out_name}.png")


src = f"{FLYER_DIR}\\feminino.jpg"
# full width row1 to find columns
fine_grid(src, (0, 380, 900, 500), "fem_row1_fullwidth", scale=2, step=5, label_step=25)
# col1 strip full height to find rows
fine_grid(src, (60, 350, 260, 1100), "fem_col1_rows_1", scale=2, step=5, label_step=25)
fine_grid(src, (60, 1050, 260, 1450), "fem_col1_rows_2", scale=2, step=5, label_step=25)
print("done")
