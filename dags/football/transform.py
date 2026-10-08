import json
from pathlib import Path
from re import match
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from team_city_map import TEAM_CITY_MAP
else:
    from dags.team_city_map import TEAM_CITY_MAP


def flatten_matches(data):
    rows = []

    for match in data["matches"]:
        city = TEAM_CITY_MAP.get(match["team1"])
        if city is None:
            raise ValueError(
                f"City for team '{match['team1']}' not found in TEAM_CITY_MAP."
            )

        full_time = match["score"].get("ft")

        if full_time is not None:
            home_score, away_score = full_time[0], full_time[1]
        else:
            home_score, away_score = None, None

        row = {
            "date": match["date"],
            "team1": match["team1"],
            "team2": match["team2"],
            "city": city,
            "home_score": home_score,
            "away_score": away_score,
        }
        rows.append(row)

    return rows


def load_all_matches(file_path=Path("include/football/raw")):
    all_rows = []

    for file in file_path.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
        league_code, season = file.stem.split("_")
        rows = flatten_matches(data)

        for row in rows:
            row["league"] = league_code
            row["season"] = season

        all_rows.extend(rows)

    return all_rows


def load_city_weather(file_path):
    with open(file_path, "r") as f:
        days = json.load(f)

    by_day = {}
    for day in days:
        by_day[day["date"]] = day

    return by_day


def load_all_weather(folder_path=Path("include/football/weather/raw")):
    weather_lookup = {}
    for file in folder_path.glob("*.json"):
        city = file.stem
        by_day = load_city_weather(file)

        for date, day in by_day.items():
            weather_lookup[(city, date)] = day
    return weather_lookup


WEATHER_LABELS = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "cloudy",
    45: "fog",
    48: "fog",
    51: "drizzle",
    53: "drizzle",
    55: "drizzle",
    61: "rain",
    63: "rain",
    65: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    80: "showers",
    81: "showers",
    82: "showers",
    95: "thunderstorm",
}


def decode_weather_code(code):
    return WEATHER_LABELS.get(code, "unknown")


def join_match_weather(match, weather_lookup):
    key = (match["city"], match["date"])
    weather = weather_lookup.get(key)
    merged = match.copy()
    if weather is None:
        merged["weather_code"] = None
        merged["temperature_2m_max"] = None
        merged["temperature_2m_min"] = None
        merged["precipitation_sum"] = None
        merged["rain_sum"] = None
        merged["snowfall_sum"] = None
        merged["precipitation_hours"] = None
        merged["wind_speed_10m_max"] = None
        merged["wind_gusts_10m_max"] = None
        merged["weather_label"] = "unknown"
    else:
        merged["weather_code"] = weather["weather_code"]
        merged["temperature_2m_max"] = weather["temperature_2m_max"]
        merged["temperature_2m_min"] = weather["temperature_2m_min"]
        merged["precipitation_sum"] = weather["precipitation_sum"]
        merged["rain_sum"] = weather["rain_sum"]
        merged["snowfall_sum"] = weather["snowfall_sum"]
        merged["precipitation_hours"] = weather["precipitation_hours"]
        merged["wind_speed_10m_max"] = weather["wind_speed_10m_max"]
        merged["wind_gusts_10m_max"] = weather["wind_gusts_10m_max"]
        merged["weather_label"] = decode_weather_code(weather["weather_code"])

    return merged


def transform():
    matches = load_all_matches()
    weather_lookup = load_all_weather()

    all_rows = []
    for match in matches:
        merged_data = join_match_weather(match, weather_lookup)
        all_rows.append(merged_data)
    return all_rows


def save_transformed_data(data, output_path=Path("include/football/transformed")):
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "transformed_data.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    transformed_data = transform()
    save_transformed_data(transformed_data)
