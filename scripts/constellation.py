"""
constellation.py
------------------
data/commits.csv icindeki gunluk commit aktivitesinden bir "takimyildizi"
gorseli uretir. Her aktif gun bir yildizdir; yildizin boyutu o gunku commit
sayisini, rengi baskin kategoriyi gosterir. Ardisik (kesintisiz) gunler ince
cizgilerle birbirine baglanir -- boylece surekli kodlama serilerin gercek bir
takimyildizi zincirine donusur, ara verdigin gunlerde zincir kopar.

assets/constellation.svg olarak kaydedilir ve README icine gomulur.
"""

import os
import math
import hashlib
import random
import pandas as pd
from datetime import timedelta

CSV_PATH = "data/commits.csv"
OUTPUT_PATH = "assets/constellation.svg"

WIDTH, HEIGHT = 800, 360
MARGIN = 50

CATEGORY_HUE = {
    "backend": 220,    # mavi
    "frontend": 320,   # pembe/mor
    "modelleme": 165,  # turkuaz
    "diger": 40,       # turuncu
}


def hsl(h, s, l, a=1.0):
    if a >= 1.0:
        return f"hsl({h:.0f}, {s:.0f}%, {l:.0f}%)"
    return f"hsla({h:.0f}, {s:.0f}%, {l:.0f}%, {a:.2f})"


def deterministic_point(seed_str: str):
    """Verilen string'den 0-1 araliginda deterministik iki sayi (x,y) uretir."""
    h = hashlib.md5(seed_str.encode()).hexdigest()
    x = int(h[:8], 16) / 0xFFFFFFFF
    y = int(h[8:16], 16) / 0xFFFFFFFF
    return x, y


def build_placeholder_svg():
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="40%" r="80%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#020617"/>
    </radialGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="20" fill="url(#bg)"/>
  <text x="{WIDTH/2}" y="{HEIGHT/2}" text-anchor="middle" fill="#94a3b8" font-family="monospace" font-size="16">
    constellation is forming — check back after a few more commits
  </text>
</svg>"""


def build_background_stars(seed: str, count: int = 70):
    rng = random.Random(seed)
    dots = []
    for _ in range(count):
        x = rng.uniform(0, WIDTH)
        y = rng.uniform(0, HEIGHT)
        r = rng.uniform(0.5, 1.4)
        opacity = rng.uniform(0.15, 0.5)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#e2e8f0" opacity="{opacity:.2f}"/>')
    return dots


def build_constellation_svg(df: pd.DataFrame, username: str) -> str:
    df["date"] = pd.to_datetime(df["date"])

    # gunluk agregasyon: her gun -> commit sayisi + baskin kategori
    daily = df.groupby(df["date"].dt.date).agg(
        count=("category", "size"),
        category=("category", lambda s: s.value_counts().idxmax()),
    ).reset_index().sort_values("date")

    max_count = daily["count"].max() or 1

    # her gun icin deterministik (x,y) konumu -- gorsele biraz "nefes payi"
    # birakmak icin kenarlardan icerlek bir alana map ediyoruz
    points = {}
    for _, row in daily.iterrows():
        date_str = str(row["date"])
        rx, ry = deterministic_point(date_str)
        x = MARGIN + rx * (WIDTH - 2 * MARGIN)
        y = MARGIN + ry * (HEIGHT - 2 * MARGIN - 40)  # altta legend icin yer birak
        points[row["date"]] = (x, y)

    # ardisik gunleri birbirine bagla (aradaki fark 1 gun ise cizgi cek)
    lines = []
    dates_sorted = list(daily["date"])
    for i in range(len(dates_sorted) - 1):
        d1, d2 = dates_sorted[i], dates_sorted[i + 1]
        if (d2 - d1) == timedelta(days=1):
            x1, y1 = points[d1]
            x2, y2 = points[d2]
            lines.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#64748b" stroke-width="1" opacity="0.5"/>'
            )

    # yildizlar
    stars = []
    for _, row in daily.iterrows():
        x, y = points[row["date"]]
        frac = row["count"] / max_count
        r = 3 + frac * 9
        hue = CATEGORY_HUE.get(row["category"], 40)
        glow_r = r + 6
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{glow_r:.1f}" fill="{hsl(hue, 80, 60, 0.18)}"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{hsl(hue, 80, 70)}"/>'
        )

    # lejant
    category_totals = df["category"].value_counts(normalize=True)
    legend = []
    lx = 40
    ly = HEIGHT - 22
    for cat, pct in category_totals.items():
        hue = CATEGORY_HUE.get(cat, 40)
        legend.append(
            f'<circle cx="{lx}" cy="{ly}" r="5" fill="{hsl(hue, 80, 65)}"/>'
            f'<text x="{lx + 12}" y="{ly + 4}" fill="#cbd5e1" '
            f'font-family="monospace" font-size="12">{cat} {pct*100:.0f}%</text>'
        )
        lx += 150

    bg_stars = build_background_stars(seed=username or "seed")

    active_days = len(daily)
    total_commits = int(daily["count"].sum())

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <radialGradient id="bg" cx="50%" cy="35%" r="85%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#020617"/>
    </radialGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="20" fill="url(#bg)"/>
  {''.join(bg_stars)}
  {''.join(lines)}
  {''.join(stars)}
  <text x="{MARGIN}" y="30" fill="#e2e8f0" font-family="monospace" font-size="13">
    commit constellation · {active_days} active days · {total_commits} commits
  </text>
  {''.join(legend)}
</svg>"""


def main():
    os.makedirs("assets", exist_ok=True)
    username = os.environ.get("GITHUB_USERNAME", "user")

    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        df = pd.DataFrame()

    if len(df) < 10:
        svg = build_placeholder_svg()
    else:
        svg = build_constellation_svg(df, username)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUTPUT_PATH} yazildi.")


if __name__ == "__main__":
    main()