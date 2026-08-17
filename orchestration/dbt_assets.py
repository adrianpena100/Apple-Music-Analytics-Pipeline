import os
from pathlib import Path
from typing import Any, Mapping

import dagster as dg
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    dbt_assets,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"

DBT_PROFILES_DIR = Path(
    os.getenv(
        "DBT_PROFILES_DIR",
        str(Path.home() / ".dbt"),
    )
)

# Allow Docker or another environment to explicitly choose
# which dbt executable Dagster should use.
#
# Local Windows development:
#     Uses dbt Fusion from ~/.local/bin/dbt.exe
#
# Docker:
#     Falls back to "dbt", which will be installed
#     in the container through requirements.txt.
DBT_EXECUTABLE_OVERRIDE = os.getenv("DBT_EXECUTABLE")

DBT_FUSION_WINDOWS = (
    Path.home()
    / ".local"
    / "bin"
    / "dbt.exe"
)

DBT_FUSION_LINUX = (
    Path.home()
    / ".local"
    / "bin"
    / "dbt"
)


if DBT_EXECUTABLE_OVERRIDE:
    DBT_EXECUTABLE = DBT_EXECUTABLE_OVERRIDE

elif DBT_FUSION_WINDOWS.exists():
    DBT_EXECUTABLE = str(DBT_FUSION_WINDOWS)

elif DBT_FUSION_LINUX.exists():
    DBT_EXECUTABLE = str(DBT_FUSION_LINUX)

else:
    DBT_EXECUTABLE = "dbt"


DBT_MANIFEST_PATH = (
    DBT_PROJECT_DIR
    / "target"
    / "manifest.json"
)


class AppleMusicDagsterDbtTranslator(
    DagsterDbtTranslator
):
    """
    Connect the dbt source table to the Dagster
    asset that loads the BigQuery raw table.

    Also organize dbt models into logical groups.
    """

    def get_asset_key(
        self,
        dbt_resource_props: Mapping[str, Any],
    ) -> dg.AssetKey:
        resource_type = dbt_resource_props.get(
            "resource_type"
        )

        resource_name = dbt_resource_props.get(
            "name"
        )

        if (
            resource_type == "source"
            and resource_name
            == "raw_apple_chart_entries"
        ):
            return dg.AssetKey(
                "load_apple_chart_bigquery"
            )

        return super().get_asset_key(
            dbt_resource_props
        )

    def get_group_name(
        self,
        dbt_resource_props: Mapping[str, Any],
    ) -> str | None:
        original_file_path = str(
            dbt_resource_props.get(
                "original_file_path",
                "",
            )
        ).replace("\\", "/")

        if (
            "models/staging/"
            in original_file_path
        ):
            return "dbt_staging"

        if (
            "models/intermediate/"
            in original_file_path
        ):
            return "dbt_intermediate"

        if (
            "models/marts/"
            in original_file_path
        ):
            return "dbt_marts"

        return super().get_group_name(
            dbt_resource_props
        )


dbt_translator = (
    AppleMusicDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(
            enable_asset_checks=True,
        )
    )
)


@dbt_assets(
    manifest=DBT_MANIFEST_PATH,
    dagster_dbt_translator=dbt_translator,
)
def apple_music_dbt_assets(
    context: dg.AssetExecutionContext,
    dbt: DbtCliResource,
):
    yield from dbt.cli(
        ["build"],
        context=context,
    ).stream()