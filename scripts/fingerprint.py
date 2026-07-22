"""
fingerprint.py
---------------
data/commits.csv icindeki commit dokusundan (saatlik yogunluk + kategori
dagilimi) yola cikarak her kullanici icin benzersiz, generative bir SVG
"parmak izi" karti uretir. assets/fingerprint.svg olarak kaydedilir ve
README icine banner gibi gomulur.

Not: Gercek kod stili analizi (satir uzunlugu, girinti, yorum sikligi) her
dosyanin diff'ini indirip parse etmeyi gerektirir; bu GitHub API rate
limit'ini hizla tuketir. Onun yerine zaten topladigimiz commit zaman/
kategori verisini kullaniyoruz -- yine de her kullanici icin farkli bir
desen cikiyor ve veri arttikca gorsel de degisiyor.
"""

import os
import math
import pandas as pd

CSV_PATH = "data/commits.csv"
OUTPUT_PATH = "assets/fingerprint.svg"

# kategori -> renk tonu (hue derece)
CATEGORY_HUE = {
    "backend": 220,    # mavi
    "frontend": 320,   # pembe/mor
    "modelleme": 165,  # turkuaz
    "diger": 40,       # turuncu
}


def hsl(h, s, l):
    return f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)"


def build_placeholder_svg():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 260" width="800" height="260">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
  </defs>
  <rect width="800" height="260" rx="18" fill="url(#bg)"/>
  <text x="400" y="135" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="16">
    fingerprint is warming up — check back after a few more commits
  </text>
</svg>"""


def build_fingerprint_svg(df: pd.DataFrame) -> str:
    width, height = 800, 320
    cx, cy = width / 2, height / 2 - 10
    inner_r, outer_r = 60, 130

    hour_counts = df.groupby("hour").size().reindex(range(24), fill_value=0)
    max_count = hour_counts.max() or 1

    hour_dominant_cat = (
        df.groupby(["hour", "category"]).size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .drop_duplicates("hour")
        .set_index("hour")["category"]
    )

    bars = []
    for hour in range(24):
        count = hour_counts[hour]
        if count == 0:
            continue
        frac = count / max_count
        bar_len = inner_r + frac * (outer_r - inner_r)
        angle = (hour / 24) * 2 * math.pi - math.pi / 2

        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + bar_len * math.cos(angle)
        y2 = cy + bar_len * math.sin(angle)

        cat = hour_dominant_cat.get(hour, "diger")
        hue = CATEGORY_HUE.get(cat, 40)
        color = hsl(hue, 70, 35 + frac * 30)

        bars.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="5" stroke-linecap="round" opacity="0.9"/>'
        )

    category_totals = df["category"].value_counts(normalize=True)
    legend = []
    lx = 40
    ly = height - 24
    for cat, pct in category_totals.items():
        hue = CATEGORY_HUE.get(cat, 40)
        legend.append(
            f'<circle cx="{lx}" cy="{ly}" r="6" fill="{hsl(hue, 70, 55)}"/>'
            f'<text x="{lx + 14}" y="{ly + 4}" fill="#cbd5e1" '
            f'font-family="monospace" font-size="12">{cat} {pct*100:.0f}%</text>'
        )
        lx += 160

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="45%" r="75%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </radialGradient>
  </defs>
  <rect width="{width}" height="{height}" rx="20" fill="url(#bg)"/>
  <circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="none" stroke="#334155" stroke-width="1"/>
  <circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="none" stroke="#334155" stroke-width="1" stroke-dasharray="2 6"/>
  {''.join(bars)}
  <text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="#e2e8f0" font-family="monospace" font-size="13">commit</text>
  <text x="{cx}" y="{cy + 14}" text-anchor="middle" fill="#e2e8f0" font-family="monospace" font-size="13">fingerprint</text>
  {''.join(legend)}
</svg>"""


def main():
    os.makedirs("assets", exist_ok=True)
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        df = pd.DataFrame()

    if len(df) < 10:
        svg = build_placeholder_svg()
    else:
        svg = build_fingerprint_svg(df)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUTPUT_PATH} yazildi.")


if __name__ == "__main__":
    main()