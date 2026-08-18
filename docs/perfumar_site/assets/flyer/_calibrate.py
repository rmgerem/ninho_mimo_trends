"""One-off calibration helper: crop test strips from the flyer to find grid boundaries."""
from PIL import Image

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"

import os
os.makedirs(OUT_DIR, exist_ok=True)

img = Image.open(f"{FLYER_DIR}\\masculino.jpg").convert("RGB")
w, h = img.size
print("size", w, h)

# Horizontal strip across full width at several y bands to find row boundaries.
for y0, y1, label in [(0, 300, "header"), (280, 420, "row1_top"), (380, 600, "row1"), (900, 1100, "arabe_header")]:
    img.crop((0, y0, w, y1)).save(f"{OUT_DIR}\\strip_{label}.png")
