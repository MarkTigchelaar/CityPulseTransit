{{ config(materialized='view') }}

with seed_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(station_id as integer) as station_id,
        cast(route_id as integer) as route_id,
        cast(platform_state as varchar(50)) as platform_state
    from {{ ref('platform_state') }}
),

live_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(station_id as integer) as station_id,
        cast(route_id as integer) as route_id,
        cast(platform_state as varchar(50)) as platform_state
    from {{ source('public_transit', 'runtime_platform_state') }}
),

combined_events as (
    select * from seed_data
    union all
    select * from live_data
)

select * from combined_events
