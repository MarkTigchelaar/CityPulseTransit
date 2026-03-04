with seed_data as (
    select * from {{ ref('platform_state') }}
),

live_data as (
    select * from {{ source('public_transit', 'runtime_platform_state') }}
),

unioned as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(station_id as integer) as station_id,
        cast(route_id as integer) as route_id,
        cast(platform_state as varchar(50)) as platform_state
    from seed_data

    union all

    select
        cast(clock_tick as integer) as clock_tick,
        cast(station_id as integer) as station_id,
        cast(route_id as integer) as route_id,
        cast(platform_state as varchar(50)) as platform_state
    from live_data
)

select
    clock_tick,
    station_id,
    route_id,
    platform_state
from unioned
