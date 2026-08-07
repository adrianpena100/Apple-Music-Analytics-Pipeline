import json
from datetime import datetime, timezone
from pathlib import Path

import requests


APPLE_RSS_URL = "https://rss.applemarketingtools.com/api/v2/us/music/most-played/50/songs.json"


def main():
    response = requests.get(APPLE_RSS_URL, timeout=30)
    response.raise_for_status()

    data = response.json()

    ingested_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = Path("data/raw") / f"apple_top_songs_us_{ingested_at}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved raw Apple chart data to: {output_path}")

    # Print a small preview so you know it worked
    results = data.get("feed", {}).get("results", [])
    print(f"Number of results: {len(results)}")

    for i, item in enumerate(results[:5], start=1):
        artist = item.get("artistName")
        name = item.get("name")
        print(f"{i}. {artist} - {name}")


if __name__ == "__main__":
    main()