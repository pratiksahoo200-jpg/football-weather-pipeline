import sys
import json
from pathlib import Path
import time
import requests

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from extract_geocoding import find_city_date
else:
    from dags.football.extract_geocoding import find_city_date


def city_coordinate(path="include/football/geocoding/city_coordinates.json"):
    with open(path, "r") as f:
        return json.load(f)


def get_city_date_range(city_dates):
    grouped_dates = {}
    for city, date in city_dates:
        if not city in grouped_dates:
            grouped_dates[city] = []
        grouped_dates[city].append(date)

    result = {}
    for city, dates in grouped_dates.items():
        result[city] = {"start_date": min(dates), "end_date": max(dates)}
    return result


def fetch_weather_for_city(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_sum,rain_sum,snowfall_sum,precipitation_hours,"
            "wind_speed_10m_max,wind_gusts_10m_max"
        ),
        "timezone": "auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def filter_needed_dates(daily, needed_dates):
    rows = []
    for position, date in enumerate(daily["time"]):
        if date in needed_dates:
            row = {"date": date}
            for name, values in daily.items():
                if name != "time":
                    row[name] = values[position]
            rows.append(row)
    return rows


def group_dates_by_city(city_dates):
    grouped_dates = {}
    for city, date in city_dates:
        if not city in grouped_dates:
            grouped_dates[city] = []
        grouped_dates[city].append(date)
    return grouped_dates


def extract_weather():
    city_dates = find_city_date()
    city_date_ranges = get_city_date_range(city_dates)
    city_coordinates = city_coordinate()
    needed_dates_by_city = group_dates_by_city(city_dates)

    weather_dir = Path("include/football/weather/raw")
    weather_dir.mkdir(parents=True, exist_ok=True)

    for city, date_range in city_date_ranges.items():
        if city not in city_coordinates:
            print(f"Skipping {city}: No coordinates found.")
            continue

        start_date = city_date_ranges[city]["start_date"]
        end_date = city_date_ranges[city]["end_date"]
        lat = city_coordinates[city]["latitude"]
        lon = city_coordinates[city]["longitude"]
        needed_dates = needed_dates_by_city[city]

        weather_path = weather_dir / f"{city}.json"

        if weather_path.exists():
            print(f"Already exists, skipping: {city}")
            continue
        try:
            result = fetch_weather_for_city(lat, lon, start_date, end_date)
            rows = filter_needed_dates(result["daily"], needed_dates)
        except requests.RequestException as e:
            print(f"Failed to fetch weather data for {city}: {e}")
            continue

        with open(weather_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

        print(f"Saved {city} ({len(rows)} days)")

        time.sleep(5)  # Sleep for 5 seconds to avoid hitting API rate limits
