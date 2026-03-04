with seed_data as (
    select * from {{ ref('world_clock_state') }}
),

live_data as (
    select * from {{ source('public_transit', 'runtime_world_clock_state') }}
),

unioned as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(year as integer) as year,
        cast(day_of_year as integer) as day_of_year,
        cast(day_of_week as varchar(10)) as day_of_week,
        cast(hour_of_day as integer) as hour_of_day,
        cast(minute as integer) as minute
    from seed_data

    union all

    select
        cast(clock_tick as integer) as clock_tick,
        cast(year as integer) as year,
        cast(day_of_year as integer) as day_of_year,
        cast(day_of_week as varchar(10)) as day_of_week,
        cast(hour_of_day as integer) as hour_of_day,
        cast(minute as integer) as minute
    from live_data
)

select
    clock_tick,
    year,
    day_of_year,
    day_of_week,
    hour_of_day,
    minute
from unioned
