"""
repo_card.py
-------------
Harici (guvenilmez, sik sik rate-limit'e takilan) servislere bagimli
kalmamak icin, katkida bulundugun bir reponun (owner/repo) bilgisini
GitHub API'den cekip kendi SVG "repo karti"ni uretir.

assets/contribution-card.svg olarak kaydedilir.

Ortam degiskeni:
- GITHUB_TOKEN        : API istekleri icin (Actions'ta otomatik gelir)
- CONTRIBUTION_REPO   : "owner/repo" formatinda, ornek: afragul/YZTA-Bootcamp
"""

import os
import requests

API_URL = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("CONTRIBUTION_REPO", "afragul/YZTA-Bootcamp")
OUTPUT_PATH = "assets/contribution-card.svg"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

LANGUAGE_COLOR = {
    "Python": "#3776AB",
    "JavaScript": "#F7DF1E",
    "TypeScript": "#3178C6",
    "Java": "#ED8B00",
    "HTML": "#E34F26",
    "CSS": "#1572B6",
    "C++": "#00599C",
    "C": "#A8B9CC",
    "Go": "#00ADD8",
    "Jupyter Notebook": "#DA5B0B",
}

WIDTH, HEIGHT = 800, 140


def build_placeholder_svg(message: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFE4EF"/>
      <stop offset="100%" stop-color="#FFC9E0"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="22" fill="url(#bg)" stroke="#F8A8C4"/>
  <text x="34" y="{HEIGHT/2 + 6}" fill="#9D174D" font-family="monospace" font-size="15">{message}</text>
</svg>"""


def build_card_svg(data: dict) -> str:
    name = data.get("full_name", REPO)
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    language = data.get("language") or "Unknown"
    lang_color = LANGUAGE_COLOR.get(language, "#9D174D")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFE4EF"/>
      <stop offset="55%" stop-color="#FFD3E6"/>
      <stop offset="100%" stop-color="#FFC1DA"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="22" fill="url(#bg)" stroke="#F8A8C4" stroke-width="1.5"/>

  <text x="34" y="56" fill="#DB2777" font-family="monospace" font-size="26" font-weight="bold">✨ {name}</text>

  <circle cx="42" cy="{HEIGHT - 30}" r="6" fill="{lang_color}"/>
  <text x="56" y="{HEIGHT - 25}" fill="#9D174D" font-family="monospace" font-size="15">{language}</text>

  <text x="220" y="{HEIGHT - 25}" fill="#9D174D" font-family="monospace" font-size="15">⭐ {stars}</text>
  <text x="320" y="{HEIGHT - 25}" fill="#9D174D" font-family="monospace" font-size="15">🍴 {forks}</text>
</svg>"""


def main():
    os.makedirs("assets", exist_ok=True)

    try:
        resp = requests.get(f"{API_URL}/repos/{REPO}", headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        svg = build_card_svg(data)
    except requests.HTTPError as e:
        print(f"Repo bilgisi alinamadi: {e}")
        svg = build_placeholder_svg(f"Could not load {REPO}")
    except requests.RequestException as e:
        print(f"Baglanti hatasi: {e}")
        svg = build_placeholder_svg(f"Could not load {REPO}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUTPUT_PATH} yazildi.")


if __name__ == "__main__":
    main()