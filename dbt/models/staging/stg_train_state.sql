with seed_data as (
    select * from {{ ref('train_state') }}
),

live_data as (
    select * from {{ source('public_transit', 'runtime_train_state') }}
),

unioned as (
    select
        cast(clock_tick as integer) as clock_tick,
        cast(train_id as integer) as train_id,
        cast(station_id as integer) as station_id,
        cast(segment_id as integer) as segment_id,
        stops_seen_so_far,
        cast(passenger_count as integer) as passenger_count
    from seed_data

    union all

    select
        cast(clock_tick as integer) as clock_tick,
        cast(train_id as integer) as train_id,
        cast(station_id as integer) as station_id,
        cast(segment_id as integer) as segment_id,
        stops_seen_so_far,
        cast(passenger_count as integer) as passenger_count
    from live_data
)

select
    clock_tick,
    train_id,
    station_id,
    segment_id,
    stops_seen_so_far,
    passenger_count
from unioned
