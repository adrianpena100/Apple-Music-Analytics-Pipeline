with snapshots as (

    select
        country,
        chart_type,
        feed_updated_at,
        max(ingested_at) as ingested_at,
        count(*) as chart_size

    from {{ ref('stg_apple_chart_entries') }}

    group by
        country,
        chart_type,
        feed_updated_at

),

final as (

    select
        country,
        chart_type,
        feed_updated_at,
        ingested_at,
        chart_size,

        row_number() over (
            partition by country, chart_type
            order by feed_updated_at
        ) as snapshot_number,

        lag(feed_updated_at) over (
            partition by country, chart_type
            order by feed_updated_at
        ) as previous_feed_updated_at

    from snapshots

)

select *
from final