"""
fetch_commits.py (v2 - Search API tabanli)
--------------------------------------------
GitHub'in commit arama API'sini (/search/commits?q=author:USERNAME) kullanarak
senin yazari oldugun TUM public commit'leri toplar -- sadece kendi
repolarindaki degil, baskasinin reposuna (fork olmadan, collaborator olarak)
attigin commit'ler de dahil.

Her commit icin: hangi repo, hangi saat, hangi gun, ve o reponun baskin
programlama diline gore bir "kategori" (backend / frontend / modelleme / diger)
bilgisini cikarip data/commits.csv dosyasina yazar.

Ortam degiskenleri (GitHub Actions tarafindan otomatik saglanir):
- GITHUB_TOKEN     : API istekleri icin (Actions'ta otomatik gelir)
- GITHUB_USERNAME  : verisi toplanacak kullanici adi (github.actor)

Not: Search API sadece PUBLIC repolari kapsar ve sonuclari en fazla 1000
commit ile sinirlar (GitHub'in kendi limiti). Private repolardaki commit'ler
bu yontemle de gorulemez -- onun icin farkli bir izin/yapilandirma gerekir.
"""

import os
import csv
import time
import requests
from datetime import datetime

API_URL = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = os.environ["GITHUB_USERNAME"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

LANGUAGE_CATEGORY = {
    "Python": "backend",
    "Java": "backend",
    "C": "backend",
    "C++": "backend",
    "C#": "backend",
    "Go": "backend",
    "Rust": "backend",
    "PHP": "backend",
    "Ruby": "backend",
    "Kotlin": "backend",
    "JavaScript": "frontend",
    "TypeScript": "frontend",
    "HTML": "frontend",
    "CSS": "frontend",
    "Vue": "frontend",
    "Svelte": "frontend",
    "Jupyter Notebook": "modelleme",
    "R": "modelleme",
}

_language_cache = {}


def gh_get(url, params=None, retries=3):
    for attempt in range(retries):
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - int(time.time()), 5)
            print(f"Rate limit asildi, {wait} saniye bekleniyor...")
            time.sleep(wait)
            continue
        if resp.status_code == 422:
            # arama sorgusunda gecersiz parametre / sonuc yok
            return {}
        resp.raise_for_status()
        return resp.json()
    return {}


def get_dominant_language(full_name: str):
    """Repo dilini cache'leyerek getirir (ayni repo icin tekrar tekrar istek atmamak icin)."""
    if full_name in _language_cache:
        return _language_cache[full_name]
    url = f"{API_URL}/repos/{full_name}/languages"
    try:
        langs = gh_get(url)
        dominant = max(langs, key=langs.get) if langs else None
    except requests.HTTPError:
        dominant = None
    _language_cache[full_name] = dominant
    return dominant


def search_all_commits():
    """Kullanicinin yazari oldugu tum public commit'leri arama API'siyla toplar."""
    all_items = []
    page = 1
    per_page = 100
    max_pages = 10  # search API en fazla 1000 sonuc veriyor (100 x 10)

    while page <= max_pages:
        url = f"{API_URL}/search/commits"
        params = {
            "q": f"author:{USERNAME}",
            "sort": "author-date",
            "order": "desc",
            "per_page": per_page,
            "page": page,
        }
        data = gh_get(url, params=params)
        items = data.get("items", [])
        if not items:
            break
        all_items.extend(items)
        print(f"  sayfa {page}: {len(items)} commit bulundu (toplam: {len(all_items)})")
        if len(items) < per_page:
            break
        page += 1

    return all_items


def main():
    print(f"{USERNAME} kullanicisi icin commit'ler araniyor (Search API)...")
    items = search_all_commits()
    print(f"Toplam {len(items)} commit bulundu.")

    rows = []
    for item in items:
        repo = item.get("repository", {})
        full_name = repo.get("full_name")
        if not full_name:
            continue

        commit_date_str = item["commit"]["author"]["date"]
        dt = datetime.strptime(commit_date_str, "%Y-%m-%dT%H:%M:%SZ")

        dominant_lang = get_dominant_language(full_name)
        category = LANGUAGE_CATEGORY.get(dominant_lang, "diger")

        rows.append({
            "repo": full_name,
            "date": dt.date().isoformat(),
            "hour": dt.hour,
            "weekday": dt.weekday(),
            "month": dt.month,
            "language": dominant_lang or "unknown",
            "category": category,
        })

    os.makedirs("data", exist_ok=True)
    with open("data/commits.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["repo", "date", "hour", "weekday", "month", "language", "category"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} satir data/commits.csv icine yazildi.")


if __name__ == "__main__":
    main()
