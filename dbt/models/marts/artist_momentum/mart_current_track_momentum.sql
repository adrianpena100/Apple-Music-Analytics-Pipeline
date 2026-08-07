with current_chart as (

    select *
    from {{ ref('fct_track_chart_history') }}

    where is_currently_charting = true

),

final as (

    select
        chart_history_key,

        apple_track_id,
        apple_artist_id,
        track_name,
        artist_name,
        primary_genre,

        country,
        chart_type,

        snapshot_number,
        snapshot_date,
        feed_updated_at,

        release_date,
        days_since_release,

        first_observed_at,
        first_observed_date,

        chart_rank as current_rank,
        previous_chart_rank,
        rank_change,
        abs(rank_change) as rank_change_magnitude,

        movement_status,

        best_rank_to_date,
        chart_appearances_to_date,

        chart_rank <= 10 as is_top_10,
        chart_rank <= 25 as is_top_25,

        case
            when movement_status = 'moved_up'
                then 'Rising'

            when movement_status = 'moved_down'
                then 'Falling'

            when movement_status = 'unchanged'
                then 'Unchanged'

            when movement_status = 'first_observed'
                then 'First observed'

            when movement_status = 're_entry'
                then 'Re-entry'

            when movement_status = 'baseline'
                then 'Baseline'

            else movement_status
        end as movement_label

    from current_chart

)

select *
from final