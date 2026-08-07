with chart_history as (

    select *
    from {{ ref('fct_track_chart_history') }}

),

snapshot_summary as (

    select
        concat(
            country,
            '|',
            chart_type,
            '|',
            cast(feed_updated_at as string)
        ) as snapshot_key,

        country,
        chart_type,

        snapshot_number,
        snapshot_date,
        feed_updated_at,

        max(is_latest_snapshot) as is_latest_snapshot,

        count(*) as total_event_count,

        countif(is_charting_in_snapshot) as charting_track_count,

        countif(movement_status = 'baseline') as baseline_count,

        countif(
            movement_status = 'first_observed'
        ) as first_observed_count,

        countif(
            movement_status = 're_entry'
        ) as re_entry_count,

        countif(
            movement_status = 'moved_up'
        ) as moved_up_count,

        countif(
            movement_status = 'moved_down'
        ) as moved_down_count,

        countif(
            movement_status = 'unchanged'
        ) as unchanged_count,

        countif(
            movement_status = 'dropped'
        ) as dropped_count,

        round(
            avg(
                case
                    when rank_change is not null
                        then abs(rank_change)
                end
            ),
            2
        ) as average_absolute_rank_change,

        max(rank_change) as largest_upward_rank_change,

        min(rank_change) as largest_downward_rank_change,

        round(
            avg(
                case
                    when is_charting_in_snapshot
                        then chart_rank
                end
            ),
            2
        ) as average_chart_rank,

        count(
            distinct case
                when is_charting_in_snapshot
                    then artist_name
            end
        ) as charting_artist_count,

        count(
            distinct case
                when is_charting_in_snapshot
                    then primary_genre
            end
        ) as represented_genre_count,

        round(
            avg(
                case
                    when is_charting_in_snapshot
                        then days_since_release
                end
            ),
            2
        ) as average_days_since_release,

        countif(
            is_charting_in_snapshot
            and days_since_release <= 30
        ) as tracks_released_last_30_days,

        countif(
            is_charting_in_snapshot
            and days_since_release >= 365
        ) as catalog_track_count

    from chart_history

    group by
        country,
        chart_type,
        snapshot_number,
        snapshot_date,
        feed_updated_at

)

select *
from snapshot_summary