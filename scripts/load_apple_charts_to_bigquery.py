import json
from pathlib import Path

from google.cloud import bigquery


PROJECT_ID = "music-analytics-500503"
DATASET_ID = "artist_momentum_raw"
TABLE_ID = "raw_apple_chart_entries"

PROCESSED_DIR = Path("data/processed")


def get_latest_processed_file() -> Path:
    files = list(PROCESSED_DIR.glob("apple_chart_entries_*.jsonl"))

    if not files:
        raise FileNotFoundError("No processed Apple chart JSONL files found in data/processed.")

    return max(files, key=lambda path: path.stat().st_mtime)


def read_jsonl(file_path: Path) -> list[dict]:
    rows = []

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    return rows


def snapshot_already_loaded(
    client: bigquery.Client,
    full_table_id: str,
    country: str,
    chart_type: str,
    feed_updated: str,
) -> bool:
    """
    Prevents loading the same Apple chart snapshot twice.

    We treat this combination as one snapshot:
    country + chart_type + feed_updated
    """

    query = f"""
        select count(*) as row_count
        from `{full_table_id}`
        where country = @country
          and chart_type = @chart_type
          and feed_updated = @feed_updated
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("country", "STRING", country),
            bigquery.ScalarQueryParameter("chart_type", "STRING", chart_type),
            bigquery.ScalarQueryParameter("feed_updated", "STRING", feed_updated),
        ]
    )

    result = client.query(query, job_config=job_config).result()
    row = next(result)

    return row.row_count > 0


def get_table_row_count(client: bigquery.Client, full_table_id: str) -> int:
    query = f"select count(*) as row_count from `{full_table_id}`"
    result = client.query(query).result()
    row = next(result)

    return row.row_count


def load_jsonl_to_bigquery(client: bigquery.Client, file_path: Path, full_table_id: str) -> None:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    with file_path.open("rb") as f:
        load_job = client.load_table_from_file(
            f,
            full_table_id,
            job_config=job_config,
        )

    load_job.result()


def main():
    latest_file = get_latest_processed_file()
    rows = read_jsonl(latest_file)

    if not rows:
        raise ValueError(f"No rows found in {latest_file}")

    first_row = rows[0]

    country = first_row["country"]
    chart_type = first_row["chart_type"]
    feed_updated = first_row["feed_updated"]

    full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    client = bigquery.Client(project=PROJECT_ID)

    print(f"Latest processed file: {latest_file}")
    print(f"Rows in file: {len(rows)}")
    print(f"Target table: {full_table_id}")
    print(f"Snapshot: country={country}, chart_type={chart_type}, feed_updated={feed_updated}")

    if snapshot_already_loaded(client, full_table_id, country, chart_type, feed_updated):
        print("This snapshot already exists in BigQuery. No rows were loaded.")
        return

    before_count = get_table_row_count(client, full_table_id)

    load_jsonl_to_bigquery(client, latest_file, full_table_id)

    after_count = get_table_row_count(client, full_table_id)

    print("Load complete.")
    print(f"Rows before: {before_count}")
    print(f"Rows after: {after_count}")
    print(f"Rows added: {after_count - before_count}")


if __name__ == "__main__":
    main()