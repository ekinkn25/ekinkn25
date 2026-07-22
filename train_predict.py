"""
train_predict.py (English version)
-----------------------------------
Trains a simple classification model using the historical commit data in
data/commits.csv and predicts which category (backend / frontend / modeling /
other) tomorrow is most likely to fall into. Turns the result into a playful
sentence and updates the marked section inside README.md.
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
    "modelleme": "🧠",  # keep matching the labels produced by fetch_commits.py
    "diger": "🔧",
}

CATEGORY_LABEL_EN = {
    "backend": "backend",
    "frontend": "frontend",
    "modelleme": "modeling",
    "diger": "other",
}


def build_fallback_message():
    return (
        f"{START_MARK}\n"
        "🤖 Not enough commit history yet to make a prediction — check back in a few days!\n"
        f"{END_MARK}"
    )


def build_prediction_message(probs_by_category: dict, tomorrow_weekday: int):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    sorted_cats = sorted(probs_by_category.items(), key=lambda x: x[1], reverse=True)
    top = sorted_cats[:2]

    parts = []
    for cat, p in top:
        emoji = CATEGORY_EMOJI.get(cat, "🔧")
        label = CATEGORY_LABEL_EN.get(cat, cat)
        parts.append(f"{p * 100:.0f}% {emoji} {label}")

    sentence = " and ".join(parts)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"{START_MARK}\n"
        f"🤖 **AI prediction** (for {days[tomorrow_weekday]}): "
        f"most likely I'll be working on {sentence}.\n\n"
        f"<sub>Last updated: {now_str} · generated using a RandomForest model "
        f"trained on my past commit data</sub>\n"
        f"{END_MARK}"
    )


def update_readme(new_block: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARK in content and END_MARK in content:
        pattern = re.compile(re.escape(START_MARK) + r".*?" + re.escape(END_MARK), re.DOTALL)
        content = pattern.sub(new_block, content)
    else:
        # if the markers are missing, just append to the end of the file
        content = content.rstrip() + "\n\n" + new_block + "\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        update_readme(build_fallback_message())
        return

    # need at least a bit of variety, otherwise the model is meaningless
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
    print("README updated:\n", message)


if __name__ == "__main__":
    main()