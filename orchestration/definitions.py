import dagster as dg
from dagster_dbt import DbtCliResource

from orchestration.assets import (
    fetch_apple_chart,
    normalize_apple_chart,
    load_apple_chart_bigquery,
)

from orchestration.dbt_assets import (
    apple_music_dbt_assets,
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    DBT_FUSION_EXECUTABLE,
)

from orchestration.schedules import (
    daily_apple_music_schedule,
)


defs = dg.Definitions(
    assets=[
        fetch_apple_chart,
        normalize_apple_chart,
        load_apple_chart_bigquery,
        apple_music_dbt_assets,
    ],
    schedules=[
        daily_apple_music_schedule,
    ],
    resources={
        "dbt": DbtCliResource(
            project_dir=DBT_PROJECT_DIR,
            profiles_dir=DBT_PROFILES_DIR,
            dbt_executable=DBT_FUSION_EXECUTABLE,
        ),
    },
)