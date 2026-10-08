import os
import json
import time
import requests
from pathlib import Path

LEAGUE_CODES = {
    "premier_league": "en.1",
    "la_liga": "es.1",
    "serie_a": "it.1",
    "bundesliga": "de.1",
}

SEASONS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]


def fetch_matches(league_code, season):
    url = f"https://raw.githubusercontent.com/openfootball/football.json/master/{season}/{league_code}.json"
    response = requests.get(url,timeout=10)
    response.raise_for_status()
    return response.json()


def extract_matches():
    raw_dir = Path("include/football/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_files = []

    for league_name, league_code in LEAGUE_CODES.items():
        for season in SEASONS:
            raw_path = raw_dir / f"{league_code}_{season}.json"

            if raw_path.exists():
                print(f"Already exists, skipping: {league_name} {season}")
                raw_files.append(raw_path)
                continue

            data = fetch_matches(league_code, season)

            with raw_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"Saved {league_name} {season}")
            raw_files.append(raw_path)

            time.sleep(0.5)

    return raw_files


if __name__ == "__main__":
    extract_matches()
