"""Generates an elegant bottle illustration (SVG) for every perfume in the catalog.

Run with: python generate_photos.py
Writes one <id>.svg per product into both photo folders used by the site:
  docs/perfumar_templates/shared/assets/products/
  docs/perfumar_site/assets/products/

Regenerate this whenever the product list changes. Real photos (.jpg/.png) dropped
into those folders always take priority over the generated illustration (see the
fallback chain in app.js / script.js).
"""
import os

PRODUCTS = [
    # Masculinos
    ("brz-urban", "BRZ Urban", "masculino"),
    ("bravus", "Bravus", "masculino"),
    ("charmy", "Charmy", "masculino"),
    ("brz-intense-men", "BRZ Intense Men", "masculino"),
    ("conquest", "Conquest", "masculino"),
    ("champion", "Champion", "masculino"),
    ("brz-men", "BRZ Men", "masculino"),
    ("elegante-sport", "Elegante Sport", "masculino"),
    ("personalz", "Personalz", "masculino"),
    ("noble", "Noble", "masculino"),
    ("blue", "Blue", "masculino"),
    ("selvagem", "Selvagem", "masculino"),
    ("sweet-class", "Sweet Class", "masculino"),
    ("silver-z", "Silver Z", "masculino"),
    ("code-man", "Code Man", "masculino"),
    ("ahazzo", "Ahazzo", "masculino"),
    ("boss-man", "Boss Man", "masculino"),
    ("mb-endless", "MB. Endless", "masculino"),
    ("jump", "Jump!", "masculino"),
    ("lord", "Lord", "masculino"),
    ("strong", "Strong", "masculino"),
    ("black-horse", "Black Horse", "masculino"),
    ("lord-green", "Lord Green", "masculino"),
    ("animalz", "Animalz", "masculino"),
    ("loyal", "Loyal", "masculino"),
    ("brz-dark", "BRZ Dark", "masculino"),
    ("tauren", "Tauren", "masculino"),
    ("valien", "Valien", "masculino"),
    # Femininos
    ("brz-blossom", "BRZ Blossom", "feminino"),
    ("brz-intense-woman", "BRZ Intense Woman", "feminino"),
    ("luminous-flowers", "Luminous Flowers", "feminino"),
    ("creta", "Creta", "feminino"),
    ("luminous-girl", "Luminous Girl", "feminino"),
    ("gold-woman", "Gold Woman", "feminino"),
    ("brz-woman", "BRZ Woman", "feminino"),
    ("lys", "Lys", "feminino"),
    ("miss", "Miss", "feminino"),
    ("love-it", "Love It", "feminino"),
    ("la-vie-est-amour", "La Vie Est Amour", "feminino"),
    ("2-love", "2 Love", "feminino"),
    ("beauty", "Beauty", "feminino"),
    ("tuberose-shine", "Tuberose Shine", "feminino"),
    ("autentica", "Autêntica", "feminino"),
    ("glow", "Glow", "feminino"),
    ("cintilante", "Cintilante", "feminino"),
    ("magic", "Magic", "feminino"),
    ("gs", "GS", "feminino"),
    ("revolution", "Revolution", "feminino"),
    ("tresor", "Trésor", "feminino"),
    ("sweet-blue", "Sweet Blue", "feminino"),
    ("sweet", "Sweet", "feminino"),
    ("unique", "Unique", "feminino"),
    ("five-z", "Five Z", "feminino"),
    ("honey", "Honey", "feminino"),
    ("aura-rose", "Aura Rose", "feminino"),
    ("isis", "Isis", "feminino"),
    # Árabes
    ("golden-arabian", "Golden Arabian", "arabe"),
    ("rubi", "Rubi", "arabe"),
    ("dunes", "Dunes", "arabe"),
    ("sunshine", "Sunshine", "arabe"),
    ("malirah", "Malirah", "arabe"),
    ("najad", "Najad", "arabe"),
    ("sharif", "Sharif", "arabe"),
    ("zayan", "Zayan", "arabe"),
    # Edições especiais
    ("primavera", "Primavera", "especial"),
    ("verao", "Verão", "especial"),
    ("outono", "Outono", "especial"),
    ("inverno", "Inverno", "especial"),
    ("yria", "Yria", "especial"),
    ("darion", "Darion", "especial"),
]

# 3 tonal variants per category so the catalog doesn't look repetitive.
PALETTES = {
    "masculino": [
        ("#333d4a", "#12161c"),
        ("#22323f", "#0e1620"),
        ("#332c26", "#181310"),
    ],
    "feminino": [
        ("#f4dad5", "#dba79b"),
        ("#f7e7ed", "#e3b9c8"),
        ("#f8ecdc", "#e8c9a0"),
    ],
    "arabe": [
        ("#ecd39a", "#b3862f"),
        ("#e6c07a", "#96631f"),
        ("#eac2ba", "#a85a52"),
    ],
    "especial": [
        ("#9b87bb", "#4a3f66"),
        ("#7fb3ba", "#2f5158"),
        ("#c19aac", "#6b3f52"),
    ],
}

BG_TINTS = {
    "masculino": ["#e7e5e1", "#e3e8ec", "#ece6df"],
    "feminino": ["#fdf3ef", "#fdf1f4", "#fdf5ea"],
    "arabe": ["#fbf1dc", "#f8ecd2", "#fbe9e6"],
    "especial": ["#f1eef7", "#eaf3f3", "#f5eef1"],
}

CAP_TOP, CAP_BOTTOM = "#e8cf8f", "#a5793a"


def wrap_name(name: str):
    """Split long names onto two lines at the nearest space to the middle."""
    if len(name) <= 13:
        return [name]
    mid = len(name) // 2
    left_space = name.rfind(" ", 0, mid)
    right_space = name.find(" ", mid)
    split_at = left_space if left_space != -1 else right_space
    if split_at == -1:
        return [name]
    return [name[:split_at], name[split_at + 1:]]


def font_size_for_lines(lines) -> int:
    longest = max(len(line) for line in lines)
    if longest <= 7:
        return 34
    if longest <= 10:
        return 29
    if longest <= 13:
        return 25
    return 21


def build_svg(product_id: str, name: str, gender: str, variant: int) -> str:
    bottle_top, bottle_bottom = PALETTES[gender][variant]
    bg_tint = BG_TINTS[gender][variant]
    lines = wrap_name(name)
    font_size = font_size_for_lines(lines)
    line_gap = font_size + 8
    label_height = 92 if len(lines) == 1 else 92 + line_gap
    label_center_y = 376 if len(lines) == 1 else 376 - line_gap / 2 + 4
    text_svg = "".join(
        f'<text x="250" y="{label_center_y + i * line_gap:.0f}" text-anchor="middle" '
        f'font-family="Georgia, \'Times New Roman\', serif" font-size="{font_size}" '
        f'font-weight="600" fill="#241d19" letter-spacing="0.3">{line}</text>'
        for i, line in enumerate(lines)
    )
    label_y = 328
    rule_top_y = label_y + 24
    rule_bottom_y = label_y + label_height - 24

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 650">
  <defs>
    <radialGradient id="bg-{product_id}" cx="50%" cy="38%" r="75%">
      <stop offset="0%" stop-color="{bg_tint}"/>
      <stop offset="100%" stop-color="{bottle_bottom}" stop-opacity="0.35"/>
    </radialGradient>
    <linearGradient id="bottle-{product_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bottle_top}"/>
      <stop offset="100%" stop-color="{bottle_bottom}"/>
    </linearGradient>
    <linearGradient id="cap-{product_id}" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{CAP_TOP}"/>
      <stop offset="100%" stop-color="{CAP_BOTTOM}"/>
    </linearGradient>
  </defs>

  <rect width="500" height="650" fill="url(#bg-{product_id})"/>

  <ellipse cx="250" cy="560" rx="130" ry="22" fill="#000000" opacity="0.18"/>

  <rect x="185" y="118" width="42" height="34" rx="6" fill="url(#cap-{product_id})"/>
  <rect x="198" y="150" width="16" height="18" fill="#cbb37a"/>

  <rect x="140" y="168" width="220" height="392" rx="26" fill="url(#bottle-{product_id})"/>
  <rect x="158" y="188" width="26" height="330" rx="13" fill="#ffffff" opacity="0.16"/>

  <rect x="150" y="{label_y}" width="200" height="{label_height:.0f}" rx="10" fill="#fdf8ee" stroke="#d9b872" stroke-width="2"/>
  <line x1="180" y1="{rule_top_y:.0f}" x2="320" y2="{rule_top_y:.0f}" stroke="#c9a24a" stroke-width="1.4"/>
  {text_svg}
  <line x1="180" y1="{rule_bottom_y:.0f}" x2="320" y2="{rule_bottom_y:.0f}" stroke="#c9a24a" stroke-width="1.4"/>

  <circle cx="90" cy="120" r="4" fill="#d9b872" opacity="0.55"/>
  <circle cx="420" cy="150" r="3" fill="#d9b872" opacity="0.45"/>
  <circle cx="410" cy="520" r="3.4" fill="#d9b872" opacity="0.4"/>
</svg>
'''


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    destinations = [
        os.path.join(here, "assets", "products"),
        os.path.normpath(os.path.join(here, "..", "..", "perfumar_site", "assets", "products")),
    ]
    for dest in destinations:
        os.makedirs(dest, exist_ok=True)

    counters = {"masculino": 0, "feminino": 0, "arabe": 0, "especial": 0}
    for product_id, name, gender in PRODUCTS:
        variant = counters[gender] % 3
        counters[gender] += 1
        svg = build_svg(product_id, name, gender, variant)
        for dest in destinations:
            with open(os.path.join(dest, f"{product_id}.svg"), "w", encoding="utf-8") as fh:
                fh.write(svg)

    print(f"Generated {len(PRODUCTS)} SVG illustrations into {len(destinations)} folders.")


if __name__ == "__main__":
    main()
