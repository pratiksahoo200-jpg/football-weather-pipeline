import json
import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


def get_postgres_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS football_weather (
            date TEXT,
            team1 TEXT,
            team2 TEXT,
            city TEXT,
            home_score INT,
            away_score INT,
            league TEXT,
            season TEXT,
            weather_code INT,
            temperature_2m_max REAL,
            temperature_2m_min REAL,
            precipitation_sum REAL,
            rain_sum REAL,
            snowfall_sum REAL,
            precipitation_hours REAL,
            wind_speed_10m_max FLOAT,
            wind_gusts_10m_max FLOAT,
            weather_label TEXT
        );
        """)

    conn.commit()


def load_transformed_data(
    file_path=Path("include/football/transformed/transformed_data.json"),
):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data


def insert_data(conn, data):
    cur = conn.cursor()
    sql = """
        INSERT INTO football_weather (date, team1, team2, city, home_score, away_score, league, season, weather_code, temperature_2m_max, temperature_2m_min, precipitation_sum, rain_sum, snowfall_sum, precipitation_hours, wind_speed_10m_max, wind_gusts_10m_max, weather_label) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for row in data:
        cur.execute(
            sql,
            (
                row["date"],
                row["team1"],
                row["team2"],
                row["city"],
                row["home_score"],
                row["away_score"],
                row["league"],
                row["season"],
                row["weather_code"],
                row["temperature_2m_max"],
                row["temperature_2m_min"],
                row["precipitation_sum"],
                row["rain_sum"],
                row["snowfall_sum"],
                row["precipitation_hours"],
                row["wind_speed_10m_max"],
                row["wind_gusts_10m_max"],
                row["weather_label"],
            ),
        )
    conn.commit()


def clear_table(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM football_weather;")
    conn.commit()


def load():
    conn = get_postgres_connection()
    create_table(conn)
    clear_table(conn)
    rows = load_transformed_data()
    insert_data(conn, rows)
    conn.close()


if __name__ == "__main__":
    load()
