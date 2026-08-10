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

DBT_PROFILES_DIR = Path.home() / ".dbt"

DBT_MANIFEST_PATH = (
    DBT_PROJECT_DIR
    / "target"
    / "manifest.json"
)

DBT_FUSION_EXECUTABLE = (
    Path.home()
    / ".local"
    / "bin"
    / "dbt.exe"
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