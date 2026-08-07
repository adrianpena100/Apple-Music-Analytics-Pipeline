with source as (

    select *
    from {{ source('apple_music', 'raw_apple_chart_entries') }}

),

renamed as (

    select
        cast(`rank` as int64) as chart_rank,

        trim(artist_name) as artist_name,
        trim(track_name) as track_name,

        cast(apple_track_id as string) as apple_track_id,
        cast(apple_artist_id as string) as apple_artist_id,

        safe_cast(release_date as date) as release_date,

        trim(primary_genre) as primary_genre,
        lower(trim(country)) as country,
        trim(chart_title) as chart_title,
        trim(chart_type) as chart_type,
        trim(kind) as media_kind,

        artist_url,
        track_url,
        artwork_url,

        case
            when content_advisory_rating = 'Explict' then 'Explicit'
            else content_advisory_rating
        end as content_advisory_rating,

        safe_cast(ingested_at as timestamp) as ingested_at,

        parse_timestamp(
            '%a, %d %b %Y %H:%M:%S %z',
            feed_updated
        ) as feed_updated_at,

        source_file,

        current_timestamp() as dbt_loaded_at

    from source

)

select *
from renamed