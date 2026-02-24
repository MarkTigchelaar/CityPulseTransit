{{ config(materialized='view') }}

with seed_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(passenger_id as integer) as passenger_id,
        cast(train_id as integer) as train_id,
        cast(station_id as integer) as station_id,
        stops_seen_so_far
    from {{ ref('passenger_state') }}
),

live_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(passenger_id as integer) as passenger_id,
        cast(train_id as integer) as train_id,
        cast(station_id as integer) as station_id,
        stops_seen_so_far
    from {{ source('public_transit', 'runtime_passenger_state') }}
),

combined_events as (
    select * from seed_data
    union all
    select * from live_data
)

select * from combined_events
