{{ config(materialized='view') }}

with 
recent_segment_logs as (
    select 
        rss.segment_id,
        rss.trains_present,
        rss.clock_tick,
        row_number() over (partition by rss.segment_id order by rss.clock_tick desc) as rn
    from {{ ref('stg_rail_segment_state') }} rss
    cross join {{ ref('int_clock__current_state') }} gc
    where rss.clock_tick >= gc.clock_tick - 5
),

latest_segments as (
    select
        segment_id,
        trains_present,
        clock_tick as last_updated_tick
    from recent_segment_logs
    where rn = 1
)

select
    ls.segment_id,
    cast(train_obj->>'id' as integer) as train_id,
    cast(train_obj->>'position_km' as numeric) as train_position, 
    ls.last_updated_tick
from latest_segments ls
left join lateral jsonb_array_elements(ls.trains_present) as train_obj on true