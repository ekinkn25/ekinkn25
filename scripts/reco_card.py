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

WIDTH, HEIGHT = 500, 170


def build_placeholder_svg(message: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="#0f172a" stroke="#334155"/>
  <text x="20" y="90" fill="#94a3b8" font-family="monospace" font-size="13">{message}</text>
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
    lang_color = LANGUAGE_COLOR.get(language, "#94a3b8")

    desc_lines = wrap_text(description, width_chars=52, max_lines=2)
    desc_svg = "".join(
        f'<text x="24" y="{78 + i * 20}" fill="#cbd5e1" font-family="monospace" font-size="13">{line}</text>'
        for i, line in enumerate(desc_lines)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="14" fill="url(#bg)" stroke="#334155"/>

  <text x="24" y="34" fill="#38BDF8" font-family="monospace" font-size="16" font-weight="bold">📌 {name}</text>

  {desc_svg}

  <circle cx="30" cy="140" r="5" fill="{lang_color}"/>
  <text x="42" y="145" fill="#e2e8f0" font-family="monospace" font-size="12">{language}</text>

  <text x="160" y="145" fill="#e2e8f0" font-family="monospace" font-size="12">⭐ {stars}</text>
  <text x="230" y="145" fill="#e2e8f0" font-family="monospace" font-size="12">🍴 {forks}</text>
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