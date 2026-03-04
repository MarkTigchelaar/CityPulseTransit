with segment_state as (
    select * from {{ ref('stg_rail_segment_state') }}
),

current_clock as (
    select * from {{ ref('int_clock_current_state') }}
),

recent_logs as (
    select
        s.segment_id,
        s.trains_present,
        s.clock_tick,
        row_number() over (
            partition by s.segment_id 
            order by s.clock_tick desc
        ) as rn
    from segment_state as s
    cross join current_clock as c
    where s.clock_tick >= c.clock_tick - 5
),

latest_segments as (
    select
        segment_id,
        trains_present,
        clock_tick as last_updated_tick
    from recent_logs
    where rn = 1
),

final as (
    select
        ls.segment_id,
        cast(train_obj ->> 'id' as integer) as train_id,
        cast(train_obj ->> 'position_km' as numeric) as train_position,
        ls.last_updated_tick
    from latest_segments as ls
    left join lateral jsonb_array_elements(ls.trains_present) as train_obj on true
)

select
    segment_id,
    train_id,
    train_position,
    last_updated_tick
from final
