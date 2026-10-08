Football Weather Pipeline

An end-to-end data engineering project that asks: can weather affect a football match?

An Apache Airflow (Astronomer) pipeline collects match results and historical weather for four European leagues, joins them, and loads them into PostgreSQL for analysis in Power BI.

Data
Source	Used for
openfootball/football.json	Match results: Premier League, La Liga, Serie A, Bundesliga, seasons 2020-21 to 2024-25
Open-Meteo Geocoding API	City coordinates for each home team
Open-Meteo Historical Weather API	Daily weather for each home city

Weather variables: weather code, max/min temperature, precipitation, rain, snowfall, precipitation hours, max wind speed, max wind gusts.

Pipeline
extract_matches -> extract_geocoding -> extract_weather -> transform -> load
extract_matches: downloads season JSON files from openfootball (skips files already downloaded)
extract_geocoding: maps each team to its city (dags/team_city_map.py) and geocodes the cities
extract_weather: one archive API call per city for its full date range, filtered to match days
transform: flattens matches, joins weather by (city, date), adds a readable weather label
load: creates and fills the football_weather table in PostgreSQL (about 7,200 rows)
Project structure
dags/
  football_dag.py          # Airflow DAG (TaskFlow API)
  team_city_map.py         # team -> home city
  football/                # extract_*, transform, load modules
include/football/          # generated data (git-ignored except geocoding)
Sample data

Generated data is not stored in the repo (the pipeline recreates it), but small samples of each stage are in sample_data/:

raw_matches_sample.json: raw match data from openfootball
raw_weather_sample.json: raw daily weather for one city from Open-Meteo
transformed_sample.json: final joined rows, one per league

Final table football_weather:

Column	Type	Description
date	text	Match date
team1 / team2	text	Home / away team
city	text	Home team's city
home_score / away_score	int	Full-time score (null if not played)
league / season	text	e.g. de.1, 2020-21
weather_code	int	WMO weather code for the day
temperature_2m_max / min	real	Daily max / min temperature (°C)
precipitation_sum, rain_sum, snowfall_sum	real	Daily totals (mm / cm)
precipitation_hours	real	Hours with precipitation
wind_speed_10m_max, wind_gusts_10m_max	float	Daily max wind speed and gusts (km/h)
weather_label	text	Readable label, e.g. rain, snow
Run it locally

Requirements: Docker, Astro CLI, and a PostgreSQL database.

Start Postgres, for example:
   docker run -d --name football-postgres -e POSTGRES_PASSWORD=change_me -e POSTGRES_DB=football_weather -p 5432:5432 postgres
Copy .env.example to .env and set your password.
Run astro dev start, open http://localhost:8080 and trigger football_dag.

The first weather run can hit Open-Meteo rate limits (HTTP 429). Cities already downloaded are cached, so re-running the task continues where it stopped.

Limitations
Weather is daily, not at kick-off time, because the match data has no kick-off times.
Weather is taken at the home team's city; teams sharing a city share its weather.
This shows association, not proof of cause.
Paths are relative to the Airflow working directory, so run it through astro dev.
Dashboard

dashboard/visual.pbix is the Power BI report that reads the football_weather table.

Credits

Match data: openfootball (public domain). Weather data: Open-Meteo.com (CC BY 4.0).