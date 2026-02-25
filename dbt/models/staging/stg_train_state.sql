{{ config(materialized='view') }}

with seed_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(train_id as integer) as train_id,
        cast(station_id as integer) as station_id,
        cast(segment_id as integer) as segment_id,
        stops_seen_so_far,
        cast(passenger_count as integer) as passenger_count
    from {{ ref('train_state') }}
),

live_data as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(train_id as integer) as train_id,
        cast(station_id as integer) as station_id,
        cast(segment_id as integer) as segment_id,
        stops_seen_so_far,
        cast(passenger_count as integer) as passenger_count
    from {{ source('public_transit', 'runtime_train_state') }}
),

combined_events as (
    select * from seed_data
    union all
    select * from live_data
)

select * from combined_events
