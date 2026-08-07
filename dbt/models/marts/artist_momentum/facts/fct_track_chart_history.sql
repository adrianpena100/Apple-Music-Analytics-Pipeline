with chart_history as (

    select *
    from {{ ref('int_chart_rank_history') }}

),

latest_snapshots as (

    select
        country,
        chart_type,
        max(snapshot_number) as latest_snapshot_number

    from chart_history

    group by
        country,
        chart_type

),

final as (

    select
        chart_history.chart_history_key,

        chart_history.apple_track_id,
        chart_history.apple_artist_id,
        chart_history.track_name,
        chart_history.artist_name,
        chart_history.primary_genre,

        chart_history.country,
        chart_history.chart_type,

        chart_history.snapshot_number,
        date(chart_history.feed_updated_at) as snapshot_date,
        
        case
            when chart_history.snapshot_number
                 = latest_snapshots.latest_snapshot_number
                then 'Latest'
            else replace(
                format_date(
                    '%b %d, %Y',
                    date(chart_history.feed_updated_at)
                ),
                ' 0',
                ' '
            )
        end as snapshot_selector,

        chart_history.feed_updated_at,
        chart_history.previous_feed_updated_at,
        chart_history.ingested_at,

        chart_history.release_date,

        case
            when chart_history.release_date is not null
                 and chart_history.release_date <= date(chart_history.feed_updated_at)
                then date_diff(
                    date(chart_history.feed_updated_at),
                    chart_history.release_date,
                    day
                )
            else null
        end as days_since_release,

        chart_history.first_observed_at,
        date(chart_history.first_observed_at) as first_observed_date,

        chart_history.chart_rank,
        chart_history.previous_chart_rank,
        chart_history.rank_change,
        chart_history.movement_status,

        case
            when chart_history.movement_status = 'baseline'
                then 'Baseline'
            when chart_history.movement_status = 'first_observed'
                then 'First observed'
            when chart_history.movement_status = 're_entry'
                then 'Re-entry'
            when chart_history.movement_status = 'moved_up'
                then 'Rising'
            when chart_history.movement_status = 'moved_down'
                then 'Falling'
            when chart_history.movement_status = 'unchanged'
                then 'Unchanged'
            when chart_history.movement_status = 'dropped'
                then 'Dropped'
            else chart_history.movement_status
        end as movement_label,

        chart_history.is_charting_in_snapshot,

        min(chart_history.chart_rank) over (
            partition by
                chart_history.apple_track_id,
                chart_history.country,
                chart_history.chart_type

            order by chart_history.snapshot_number

            rows between unbounded preceding and current row
        ) as best_rank_to_date,

        countif(chart_history.is_charting_in_snapshot) over (
            partition by
                chart_history.apple_track_id,
                chart_history.country,
                chart_history.chart_type

            order by chart_history.snapshot_number

            rows between unbounded preceding and current row
        ) as chart_appearances_to_date,

        chart_history.snapshot_number
            = latest_snapshots.latest_snapshot_number
            as is_latest_snapshot,

        chart_history.snapshot_number
            = latest_snapshots.latest_snapshot_number
            and chart_history.is_charting_in_snapshot
            as is_currently_charting

    from chart_history

    inner join latest_snapshots
        on chart_history.country = latest_snapshots.country
        and chart_history.chart_type = latest_snapshots.chart_type

)

select *
from final