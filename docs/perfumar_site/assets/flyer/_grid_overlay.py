"""One-off calibration helper: overlay a labeled grid on the flyer to read exact pixel coordinates."""
from PIL import Image, ImageDraw

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"

for name in ("masculino", "feminino"):
    img = Image.open(f"{FLYER_DIR}\\{name}.jpg").convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    for y in range(0, h, 20):
        color = (255, 0, 0) if y % 100 == 0 else (0, 200, 255)
        draw.line([(0, y), (w, y)], fill=color, width=1)
        if y % 100 == 0:
            draw.text((4, y + 2), str(y), fill=(255, 0, 0))
    for x in range(0, w, 50):
        color = (255, 0, 0) if x % 100 == 0 else (0, 200, 255)
        draw.line([(x, 0), (x, h)], fill=color, width=1)
        if x % 100 == 0:
            draw.text((x + 2, 2), str(x), fill=(255, 0, 0))
    img.save(f"{OUT_DIR}\\grid_{name}.png")
print("done")
