"""
weekly_summary.py
------------------
data/commits.csv icindeki bu haftanin (Pazartesi -> bugun) verisinden bir
ozet cikarip README.md icindeki isaretli bolumu gunceller.
"""

import re
import pandas as pd
from datetime import datetime, timedelta

CSV_PATH = "data/commits.csv"
README_PATH = "README.md"
START_MARK = "<!--START_SECTION:weekly-summary-->"
END_MARK = "<!--END_SECTION:weekly-summary-->"

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_fallback():
    return f"{START_MARK}\n📊 No commits logged yet this week.\n{END_MARK}"


def build_summary(df: pd.DataFrame) -> str:
    total = len(df)
    top_lang = df["language"].value_counts().idxmax() if "language" in df.columns else "unknown"
    top_cat = df["category"].value_counts().idxmax()

    day_counts = df.groupby("weekday").size()
    best_day_idx = int(day_counts.idxmax())
    best_day = WEEKDAY_NAMES[best_day_idx]
    best_day_count = int(day_counts.max())

    return (
        f"{START_MARK}\n"
        f"📊 **This week:** {total} commits · mostly in **{top_lang}** ({top_cat}) · "
        f"most productive day so far: **{best_day}** ({best_day_count} commits)\n"
        f"{END_MARK}"
    )


def update_readme(new_block: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARK in content and END_MARK in content:
        pattern = re.compile(re.escape(START_MARK) + r".*?" + re.escape(END_MARK), re.DOTALL)
        content = pattern.sub(new_block, content)
    else:
        content = content.rstrip() + "\n\n" + new_block + "\n"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        update_readme(build_fallback())
        return

    if df.empty:
        update_readme(build_fallback())
        return

    df["date"] = pd.to_datetime(df["date"])
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    this_week = df[df["date"].dt.date >= monday]

    if this_week.empty:
        update_readme(build_fallback())
        return

    update_readme(build_summary(this_week))


if __name__ == "__main__":
    main()