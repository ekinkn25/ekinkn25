"""
train_predict.py
-----------------
data/commits.csv icindeki gecmis commit verisiyle basit bir siniflandirma
modeli egitir ve "yarin" hangi kategoride (backend / frontend / modelleme / diger)
calisma ihtimalinin yuksek oldugunu tahmin eder. Sonucu esprili bir cumleye
donusturup README.md icindeki isaretli bolumu gunceller.
"""

import re
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier

CSV_PATH = "data/commits.csv"
README_PATH = "README.md"
START_MARK = "<!--START_SECTION:ml-prediction-->"
END_MARK = "<!--END_SECTION:ml-prediction-->"

CATEGORY_EMOJI = {
    "backend": "⚙️",
    "frontend": "🎨",
    "modelleme": "🧠",
    "diger": "🔧",
}


def build_fallback_message():
    return (
        f"{START_MARK}\n"
        "🤖 Henuz tahmin yapacak kadar commit verim yok, birkaç gün sonra tekrar bak!\n"
        f"{END_MARK}"
    )


def build_prediction_message(probs_by_category: dict, tomorrow_weekday: int):
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    sorted_cats = sorted(probs_by_category.items(), key=lambda x: x[1], reverse=True)
    top = sorted_cats[:2]

    parts = []
    for cat, p in top:
        emoji = CATEGORY_EMOJI.get(cat, "🔧")
        parts.append(f"%{p * 100:.0f} {emoji} {cat}")

    cumle = " ve ".join(parts)
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    return (
        f"{START_MARK}\n"
        f"🤖 **Yapay zeka tahmini** ({gunler[tomorrow_weekday]} için): "
        f"büyük ihtimalle {cumle} üzerinde çalışacağım.\n\n"
        f"<sub>Son güncelleme: {now_str} · geçmiş commit verilerimle eğitilmiş bir "
        f"RandomForest modeliyle üretildi</sub>\n"
        f"{END_MARK}"
    )


def update_readme(new_block: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARK in content and END_MARK in content:
        pattern = re.compile(re.escape(START_MARK) + r".*?" + re.escape(END_MARK), re.DOTALL)
        content = pattern.sub(new_block, content)
    else:
        # isaretler yoksa dosyanin sonuna ekle
        content = content.rstrip() + "\n\n" + new_block + "\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        update_readme(build_fallback_message())
        return

    # en az birkac farkli gunde commit atilmis olmali, yoksa model anlamsiz olur
    if len(df) < 15 or df["category"].nunique() < 2:
        update_readme(build_fallback_message())
        return

    X = df[["weekday", "month"]]
    y = df["category"]

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)

    tomorrow = datetime.now() + timedelta(days=1)
    X_tomorrow = pd.DataFrame([{
        "weekday": tomorrow.weekday(),
        "month": tomorrow.month,
    }])

    proba = model.predict_proba(X_tomorrow)[0]
    probs_by_category = dict(zip(model.classes_, proba))

    message = build_prediction_message(probs_by_category, tomorrow.weekday())
    update_readme(message)
    print("README guncellendi:\n", message)


if __name__ == "__main__":
    main()