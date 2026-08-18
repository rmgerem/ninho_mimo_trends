"""One-off helper: finds the white content panel bounds in the flyer photos
so we can compute an accurate product grid for cropping. Not used at runtime."""
from PIL import Image
import numpy as np

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"


def find_white_panel(path):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    # "white-ish": all channels high and close to each other (paper), ignoring background gradient.
    is_white = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 200) & (arr[:, :, 2] > 200)
    row_frac = is_white.mean(axis=1)
    col_frac = is_white.mean(axis=0)
    rows = np.where(row_frac > 0.5)[0]
    cols = np.where(col_frac > 0.5)[0]
    return {
        "size": img.size,
        "top": int(rows.min()) if len(rows) else None,
        "bottom": int(rows.max()) if len(rows) else None,
        "left": int(cols.min()) if len(cols) else None,
        "right": int(cols.max()) if len(cols) else None,
    }


for name in ("masculino.jpg", "feminino.jpg"):
    print(name, find_white_panel(f"{FLYER_DIR}\\{name}"))
