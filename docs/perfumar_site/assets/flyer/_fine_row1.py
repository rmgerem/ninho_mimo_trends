"""One-off calibration: fine grid over full width of row 1 to nail column boundaries precisely."""
from PIL import Image, ImageDraw

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"


def fine_grid(src, box, out_name, scale=2, step=10, label_step=50):
    img = Image.open(src).convert("RGB").crop(box)
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    ox, oy = box[0], box[1]
    for y in range(0, img.height, step * scale):
        orig_y = oy + y // scale
        color = (255, 0, 0) if orig_y % label_step == 0 else (0, 200, 255)
        draw.line([(0, y), (img.width, y)], fill=color, width=1)
    for x in range(0, img.width, step * scale):
        orig_x = ox + x // scale
        color = (255, 0, 0) if orig_x % label_step == 0 else (0, 200, 255)
        draw.line([(x, 0), (x, img.height)], fill=color, width=1)
        if orig_x % label_step == 0:
            draw.text((x + 1, 1), str(orig_x), fill=(255, 0, 0))
    img.save(f"{OUT_DIR}\\{out_name}.png")


fine_grid(f"{FLYER_DIR}\\masculino.jpg", (0, 460, 900, 565), "fine_row1_fullwidth", scale=2, step=5, label_step=25)
print("done")
