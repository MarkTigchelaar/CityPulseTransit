{{ config(materialized='table') }}

select
    clock_tick,
    passenger_id,
    train_id,
    station_id,
    number_of_stops_seen
from
    {{ ref('passenger_state') }}
