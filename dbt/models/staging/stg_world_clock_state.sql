{{ config(materialized='view') }}

with seed_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(year as integer) as year,
        cast(day_of_year as integer) as day_of_year,
        cast(day_of_week as varchar(10)) as day_of_week,
        cast(hour_of_day as integer) as hour_of_day,
        cast(minute as integer) as minute
    from {{ ref('world_clock_state') }}
),

live_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(year as integer) as year,
        cast(day_of_year as integer) as day_of_year,
        cast(day_of_week as varchar(10)) as day_of_week,
        cast(hour_of_day as integer) as hour_of_day,
        cast(minute as integer) as minute
    from {{ source('public_transit', 'runtime_world_clock_state') }}
),

combined_events as (
    select * from seed_data
    union all
    select * from live_data
)

select * from combined_events
