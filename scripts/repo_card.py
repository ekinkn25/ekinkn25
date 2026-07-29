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
import textwrap
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

WIDTH, HEIGHT = 800, 200


def build_placeholder_svg(message: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#3d2436"/>
      <stop offset="100%" stop-color="#2a1a26"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="url(#bg)" stroke="#7c4a63"/>
  <text x="30" y="{HEIGHT/2}" fill="#e9c9d6" font-family="monospace" font-size="14">{message}</text>
</svg>"""


def wrap_text(text: str, width_chars: int, max_lines: int):
    if not text:
        return []
    wrapped = textwrap.wrap(text, width=width_chars)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip() + "..."
    return wrapped


def build_card_svg(data: dict) -> str:
    name = data.get("full_name", REPO)
    description = data.get("description") or "No description provided."
    stars = data.get("stargazers_count", 0)
    forks = data.get("forks_count", 0)
    language = data.get("language") or "Unknown"
    lang_color = LANGUAGE_COLOR.get(language, "#e9c9d6")

    desc_lines = wrap_text(description, width_chars=85, max_lines=2)
    desc_svg = "".join(
        f'<text x="34" y="{100 + i * 26}" fill="#e9c9d6" font-family="monospace" font-size="16">{line}</text>'
        for i, line in enumerate(desc_lines)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4a2c3d"/>
      <stop offset="55%" stop-color="#3d2436"/>
      <stop offset="100%" stop-color="#2a1a26"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="url(#bg)" stroke="#7c4a63"/>

  <text x="34" y="52" fill="#F9A8D4" font-family="monospace" font-size="24" font-weight="bold">📌 {name}</text>

  {desc_svg}

  <circle cx="42" cy="{HEIGHT - 32}" r="6" fill="{lang_color}"/>
  <text x="56" y="{HEIGHT - 27}" fill="#f3e3ea" font-family="monospace" font-size="15">{language}</text>

  <text x="220" y="{HEIGHT - 27}" fill="#f3e3ea" font-family="monospace" font-size="15">⭐ {stars}</text>
  <text x="320" y="{HEIGHT - 27}" fill="#f3e3ea" font-family="monospace" font-size="15">🍴 {forks}</text>
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