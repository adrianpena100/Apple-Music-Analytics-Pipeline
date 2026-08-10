import dagster as dg

from scripts.fetch_apple_charts import (
    fetch_apple_chart_data,
)
from scripts.normalize_apple_charts import (
    normalize_apple_chart_data,
)
from scripts.load_apple_charts_to_bigquery import (
    load_apple_chart_to_bigquery,
)


@dg.asset(
    group_name="ingestion",
    description=(
        "Fetches the latest Apple Music US chart "
        "and saves the raw JSON locally."
    ),
)
def fetch_apple_chart(
    context: dg.AssetExecutionContext,
) -> str:
    context.log.info(
        "Fetching Apple Music chart..."
    )

    output_path = fetch_apple_chart_data()

    context.log.info(
        f"Apple Music chart saved to {output_path}"
    )

    context.add_output_metadata(
        {
            "raw_file_path": dg.MetadataValue.path(
                str(output_path)
            ),
        }
    )

    return str(output_path)


@dg.asset(
    group_name="ingestion",
    description=(
        "Normalizes the raw Apple Music chart "
        "into newline-delimited JSON."
    ),
)
def normalize_apple_chart(
    context: dg.AssetExecutionContext,
    fetch_apple_chart: str,
) -> str:
    context.log.info(
        "Normalizing raw chart file: "
        f"{fetch_apple_chart}"
    )

    output_path = normalize_apple_chart_data(
        fetch_apple_chart
    )

    context.log.info(
        f"Normalized chart saved to {output_path}"
    )

    context.add_output_metadata(
        {
            "processed_file_path": (
                dg.MetadataValue.path(
                    str(output_path)
                )
            ),
        }
    )

    return str(output_path)


@dg.asset(
    group_name="warehouse",
    description=(
        "Loads the normalized Apple Music chart "
        "snapshot into the BigQuery raw table."
    ),
)
def load_apple_chart_bigquery(
    context: dg.AssetExecutionContext,
    normalize_apple_chart: str,
) -> str:
    context.log.info(
        "Loading processed chart file into BigQuery: "
        f"{normalize_apple_chart}"
    )

    load_result = load_apple_chart_to_bigquery(
        normalize_apple_chart
    )

    context.add_output_metadata(
        {
            "target_table": (
                load_result["table"]
            ),
            "snapshot_loaded": (
                load_result["loaded"]
            ),
            "rows_in_file": (
                load_result["rows_in_file"]
            ),
            "rows_added": (
                load_result["rows_added"]
            ),
            "country": (
                load_result["country"]
            ),
            "chart_type": (
                load_result["chart_type"]
            ),
            "feed_updated": (
                load_result["feed_updated"]
            ),
        }
    )

    if load_result["loaded"]:
        context.log.info(
            "BigQuery load completed successfully. "
            f"{load_result['rows_added']} rows added."
        )
    else:
        context.log.info(
            "Snapshot already existed in BigQuery. "
            "No duplicate rows were added."
        )

    return load_result["table"]