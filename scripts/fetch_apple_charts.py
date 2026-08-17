import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


APPLE_RSS_URL = (
    "https://rss.applemarketingtools.com/api/v2/"
    "us/music/most-played/50/songs.json"
)

MAX_ATTEMPTS = 3
CONNECT_TIMEOUT_SECONDS = 10
READ_TIMEOUT_SECONDS = 60


def fetch_apple_chart_data() -> Path:
    """
    Fetch the latest Apple Music Top 50 chart.

    The request is retried because temporary network/API
    slowdowns should not immediately fail the daily pipeline.
    """

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(
                f"Fetching Apple Music chart "
                f"(attempt {attempt}/{MAX_ATTEMPTS})..."
            )

            response = requests.get(
                APPLE_RSS_URL,
                timeout=(
                    CONNECT_TIMEOUT_SECONDS,
                    READ_TIMEOUT_SECONDS,
                ),
            )

            response.raise_for_status()

            data = response.json()

            results = data.get("feed", {}).get("results", [])

            if not results:
                raise ValueError(
                    "Apple Music response contained no chart results."
                )

            print(
                f"Apple Music request succeeded on attempt {attempt}."
            )

            break

        except (
            requests.exceptions.RequestException,
            ValueError,
        ) as error:
            last_error = error

            print(
                f"Attempt {attempt} failed: "
                f"{type(error).__name__}: {error}"
            )

            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    "Unable to fetch the Apple Music chart "
                    f"after {MAX_ATTEMPTS} attempts."
                ) from last_error

            wait_seconds = 5 * (2 ** (attempt - 1))

            print(
                f"Waiting {wait_seconds} seconds "
                "before retrying..."
            )

            time.sleep(wait_seconds)

    ingested_at = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    output_path = (
        Path("data/raw")
        / f"apple_top_songs_us_{ingested_at}.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
        )

    print(
        f"Saved raw Apple chart data to: {output_path}"
    )

    results = data.get(
        "feed",
        {},
    ).get(
        "results",
        [],
    )

    print(
        f"Number of results: {len(results)}"
    )

    for i, item in enumerate(
        results[:5],
        start=1,
    ):
        artist = item.get("artistName")
        name = item.get("name")

        print(
            f"{i}. {artist} - {name}"
        )

    return output_path


def main() -> None:
    fetch_apple_chart_data()


if __name__ == "__main__":
    main()