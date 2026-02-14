{{ config(materialized='table') }}

select
    train_id,
    clock_tick,
    station_id,
    segment_id,
    number_of_stops_seen,
    passenger_count
from {{ ref('train_state') }}
