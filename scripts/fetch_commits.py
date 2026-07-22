import os
import requests

GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "ekinkn25"

def get_commit_events():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    url = f"https://api.github.com/users/{USERNAME}/events/public"
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []