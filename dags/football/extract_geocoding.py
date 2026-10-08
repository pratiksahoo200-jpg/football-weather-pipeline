import json
from os import mkdir
from pathlib import Path
import sys
import requests
import os

# Support both direct execution (``python dags/football/extract_geocoding.py``)
# and importing this file from the Airflow DAG package.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from team_city_map import TEAM_CITY_MAP
else:
    from dags.team_city_map import TEAM_CITY_MAP


def load_teams(file_path=Path("include/football/raw")):
    teams = set()
    for file in file_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for match in data["matches"]:
            teams.add(match["team1"])
            teams.add(match["team2"])

    teams = sorted(teams)
    print(f"Total unique teams: {len(teams)}")
    print(teams)
    return teams


def get_unique_cities(teams):
    cities = set()
    for team in teams:
        city = TEAM_CITY_MAP.get(team)
        if city is not None:
            cities.add(city)
        else:
            raise ValueError(f"City for team '{team}' not found in TEAM_CITY_MAP.")
    return cities


CITY_OVERRIDES = {
    "Venice": {"city": "Venice", "latitude": 45.4408, "longitude": 12.3155},
    "Palma de Mallorca": {
        "city": "Palma de Mallorca",
        "latitude": 39.5696,
        "longitude": 2.6502,
    },
    "San Sebastián": {
        "city": "San Sebastián",
        "latitude": 43.3183,
        "longitude": -1.9812,
    },
    "Villarreal": {"city": "Villarreal", "latitude": 39.93778, "longitude": -0.10139},
}
# i put this here because geocoding api is not returning the correct coordinates for these cities,
# so we need to override them with the correct coordinates.


def geocode_city(city_name):
    # Check if the city has an override
    if city_name in CITY_OVERRIDES:
        return CITY_OVERRIDES[city_name]

    url = "https://geocoding-api.open-meteo.com/v1/search"
    response = requests.get(url, params={"name": city_name, "count": 1}, timeout=10)
    response.raise_for_status()
    data = response.json()
    if "results" in data and len(data["results"]) > 0:
        result = data["results"][0]
        return {
            "city": city_name,
            "latitude": result["latitude"],
            "longitude": result["longitude"],
        }
    else:
        return {"city": city_name, "latitude": None, "longitude": None}


def build_city_coordinates(cities):
    city_coordinates = {}
    for city in cities:
        geocoded_info = geocode_city(city)
        city_coordinates[city] = geocoded_info
        print(f"Geocoded {city}: {geocoded_info}")

    os.makedirs("include/football/geocoding", exist_ok=True)
    with open("include/football/geocoding/city_coordinates.json", "w") as f:
        json.dump(city_coordinates, f, indent=2)

    return city_coordinates


def find_city_date(file_path=Path("include/football/raw")):
    """Return the unique home-city and match-date combinations in raw data."""
    city_dates = set()
    for file in file_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for match in data["matches"]:
            city = TEAM_CITY_MAP.get(match["team1"])
            date = match["date"]
            if city is not None:
                city_dates.add((city, date))
            else:
                raise ValueError(
                    f"City for team '{match['team1']}' not found in TEAM_CITY_MAP."
                )

    print(f"Total unique city-date combinations: {len(city_dates)}")
    print("Sample city-date combinations:", sorted(city_dates)[:10])
    return city_dates


def extract_geocoding():
    city_dates = find_city_date()
    teams = load_teams()
    cities = get_unique_cities(teams)
    print(f"Total unique cities: {len(cities)}")

    city_coordinates = build_city_coordinates(cities)
    return city_coordinates


if __name__ == "__main__":
    extract_geocoding()
