with chart_entries as (

    select
        apple_track_id,
        apple_artist_id,
        track_name,
        artist_name,
        country,
        chart_type,
        primary_genre,
        release_date,
        chart_rank,
        feed_updated_at,
        ingested_at

    from {{ ref('stg_apple_chart_entries') }}

),

snapshots as (

    select *
    from {{ ref('int_chart_snapshots') }}

),

first_observations as (

    select
        apple_track_id,
        country,
        chart_type,
        min(feed_updated_at) as first_observed_at

    from chart_entries

    group by
        apple_track_id,
        country,
        chart_type

),

appearance_comparisons as (

    select
        current_entry.apple_track_id,
        current_entry.apple_artist_id,
        current_entry.track_name,
        current_entry.artist_name,
        current_entry.country,
        current_entry.chart_type,
        current_entry.primary_genre,
        current_entry.release_date,

        snapshot.snapshot_number,
        current_entry.feed_updated_at,
        current_entry.ingested_at,
        first_observation.first_observed_at,

        current_entry.chart_rank,
        snapshot.previous_feed_updated_at,
        previous_entry.chart_rank as previous_chart_rank

    from chart_entries as current_entry

    inner join snapshots as snapshot
        on current_entry.country = snapshot.country
        and current_entry.chart_type = snapshot.chart_type
        and current_entry.feed_updated_at = snapshot.feed_updated_at

    inner join first_observations as first_observation
        on current_entry.apple_track_id = first_observation.apple_track_id
        and current_entry.country = first_observation.country
        and current_entry.chart_type = first_observation.chart_type

    left join chart_entries as previous_entry
        on current_entry.apple_track_id = previous_entry.apple_track_id
        and current_entry.country = previous_entry.country
        and current_entry.chart_type = previous_entry.chart_type
        and previous_entry.feed_updated_at = snapshot.previous_feed_updated_at

),

appearance_events as (

    select
        apple_track_id,
        apple_artist_id,
        track_name,
        artist_name,
        country,
        chart_type,
        primary_genre,
        release_date,

        snapshot_number,
        feed_updated_at,
        ingested_at,
        first_observed_at,

        chart_rank,
        previous_feed_updated_at,
        previous_chart_rank,

        previous_chart_rank - chart_rank as rank_change,

        case
            when snapshot_number = 1
                then 'baseline'

            when previous_chart_rank is null
                 and feed_updated_at > first_observed_at
                then 're_entry'

            when previous_chart_rank is null
                then 'first_observed'

            when chart_rank < previous_chart_rank
                then 'moved_up'

            when chart_rank > previous_chart_rank
                then 'moved_down'

            else 'unchanged'
        end as movement_status,

        true as is_charting_in_snapshot

    from appearance_comparisons

),

drop_events as (

    select
        previous_entry.apple_track_id,
        previous_entry.apple_artist_id,
        previous_entry.track_name,
        previous_entry.artist_name,
        previous_entry.country,
        previous_entry.chart_type,
        previous_entry.primary_genre,
        previous_entry.release_date,

        current_snapshot.snapshot_number,
        current_snapshot.feed_updated_at,
        current_snapshot.ingested_at,
        first_observation.first_observed_at,

        cast(null as int64) as chart_rank,
        current_snapshot.previous_feed_updated_at,
        previous_entry.chart_rank as previous_chart_rank,

        cast(null as int64) as rank_change,
        'dropped' as movement_status,
        false as is_charting_in_snapshot

    from snapshots as current_snapshot

    inner join chart_entries as previous_entry
        on previous_entry.country = current_snapshot.country
        and previous_entry.chart_type = current_snapshot.chart_type
        and previous_entry.feed_updated_at = current_snapshot.previous_feed_updated_at

    inner join first_observations as first_observation
        on previous_entry.apple_track_id = first_observation.apple_track_id
        and previous_entry.country = first_observation.country
        and previous_entry.chart_type = first_observation.chart_type

    left join chart_entries as current_entry
        on previous_entry.apple_track_id = current_entry.apple_track_id
        and previous_entry.country = current_entry.country
        and previous_entry.chart_type = current_entry.chart_type
        and current_entry.feed_updated_at = current_snapshot.feed_updated_at

    where current_snapshot.previous_feed_updated_at is not null
      and current_entry.apple_track_id is null

),

all_events as (

    select *
    from appearance_events

    union all

    select *
    from drop_events

),

final as (

    select
        concat(
            country,
            '|',
            chart_type,
            '|',
            cast(feed_updated_at as string),
            '|',
            apple_track_id
        ) as chart_history_key,

        *

    from all_events

)

select *
from final