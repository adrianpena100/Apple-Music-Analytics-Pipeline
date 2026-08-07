import json
from datetime import datetime, timezone
from pathlib import Path


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def get_latest_raw_file() -> Path:
    files = list(RAW_DIR.glob("apple_top_songs_us_*.json"))

    if not files:
        raise FileNotFoundError("No raw Apple chart files found in data/raw.")

    return max(files, key=lambda path: path.stat().st_mtime)


def get_primary_genre(genres: list[dict]) -> str | None:
    """
    Apple includes a generic 'Music' genre.
    We want the more specific genre like Pop, Country, Hip-Hop/Rap, etc.
    """
    for genre in genres:
        if genre.get("name") != "Music":
            return genre.get("name")

    return genres[0].get("name") if genres else None


def main():
    latest_file = get_latest_raw_file()

    with latest_file.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    feed = raw_data.get("feed", {})
    results = feed.get("results", [])

    if not results:
        raise ValueError(f"No chart results found in raw file: {latest_file}")

    feed_updated = feed.get("updated")
    country = feed.get("country")
    chart_title = feed.get("title")

    normalized_rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    for rank, item in enumerate(results, start=1):
        genres = item.get("genres", [])

        row = {
            "ingested_at": ingested_at,
            "feed_updated": feed_updated,
            "country": country,
            "chart_title": chart_title,
            "chart_type": "most-played-songs",
            "rank": rank,
            "apple_track_id": item.get("id"),
            "track_name": item.get("name"),
            "artist_name": item.get("artistName"),
            "apple_artist_id": item.get("artistId"),
            "release_date": item.get("releaseDate"),
            "kind": item.get("kind"),
            "primary_genre": get_primary_genre(genres),
            "artist_url": item.get("artistUrl"),
            "track_url": item.get("url"),
            "artwork_url": item.get("artworkUrl100"),
            "content_advisory_rating": item.get("contentAdvisoryRating"),
            "source_file": latest_file.name,
        }

        normalized_rows.append(row)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file = PROCESSED_DIR / f"apple_chart_entries_{timestamp}.jsonl"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        for row in normalized_rows:
            f.write(json.dumps(row) + "\n")

    print(f"Read raw file: {latest_file}")
    print(f"Wrote normalized rows to: {output_file}")
    print(f"Number of rows: {len(normalized_rows)}")

    print("\nPreview:")
    for row in normalized_rows[:5]:
        print(f"{row['rank']}. {row['artist_name']} - {row['track_name']} ({row['primary_genre']})")


if __name__ == "__main__":
    main()