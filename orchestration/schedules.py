import dagster as dg

from orchestration.assets import (
    fetch_apple_chart,
    normalize_apple_chart,
    load_apple_chart_bigquery,
)

from orchestration.dbt_assets import (
    apple_music_dbt_assets,
)


daily_apple_music_schedule = dg.ScheduleDefinition(
    name="daily_apple_music_pipeline",
    cron_schedule="30 2 * * *",
    execution_timezone="America/Chicago",
    target=[
        fetch_apple_chart,
        normalize_apple_chart,
        load_apple_chart_bigquery,
        apple_music_dbt_assets,
    ],
)