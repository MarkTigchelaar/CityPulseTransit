with source as (
    select * from {{ ref('stg_world_clock_state') }}
),

latest_tick as (
    select 
        max(clock_tick) as clock_tick 
    from source
),

final as (
    select
        s.clock_tick,
        s.year,
        s.day_of_year,
        s.day_of_week,
        s.hour_of_day,
        s.minute
    from source as s
    inner join latest_tick as l on s.clock_tick = l.clock_tick
)

select
    clock_tick,
    year,
    day_of_year,
    day_of_week,
    hour_of_day,
    minute
from final
