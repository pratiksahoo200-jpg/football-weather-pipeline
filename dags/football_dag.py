from airflow.sdk import dag, task
from pendulum import datetime


@dag(
    dag_id="football_dag",
    start_date=datetime(2026, 10, 4),
    schedule="@daily",
    catchup=False,
)
def football_dag():
    @task
    def extract_matches_task():
        from football.extract_matches import extract_matches

        extract_matches()

    @task
    def extract_geocoding_task():
        from football.extract_geocoding import extract_geocoding

        extract_geocoding()

    @task
    def extract_weather_task():
        from football.extract_weather import extract_weather

        extract_weather()

    @task
    def transform_task():
        from football.transform import transform, save_transformed_data

        data = transform()
        save_transformed_data(data)

    @task
    def load_task():
        from football.load import load

        load()

    matches = extract_matches_task()
    geocoding = extract_geocoding_task()
    weather = extract_weather_task()
    transformed = transform_task()
    loaded = load_task()

    matches >> geocoding >> weather >> transformed >> loaded


football_dag()
