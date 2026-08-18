from PIL import Image, ImageDraw

FLYER_DIR = r"c:\Projetos\musicville\ninho_mimo_trends\docs\perfumar_site\assets\flyer"
OUT_DIR = FLYER_DIR + r"\_calib"


def fine_grid(src, box, out_name, scale=3, step=5, label_step=25):
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
    for x in range(0, img.width, step * scale):
        orig_x = ox + x // scale
        color = (255, 0, 0) if orig_x % label_step == 0 else (0, 200, 255)
        draw.line([(x, 0), (x, img.height)], fill=color, width=1)
        if orig_x % label_step == 0:
            draw.text((x + 1, 1), str(orig_x), fill=(255, 0, 0))
    img.save(f"{OUT_DIR}\\{out_name}.png")


src = f"{FLYER_DIR}\\feminino.jpg"
fine_grid(src, (450, 1150, 900, 1280), "fem_noblesse_only")
fine_grid(src, (0, 1150, 500, 1330), "fem_estacoes_only")
print("done")
