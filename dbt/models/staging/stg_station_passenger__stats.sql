{{ config(materialized='view') }}

select
  station_id,
  clock_tick,
  total_passengers_in_station,
  passengers_boarded_trains,
  passengers_entered_station,
  passengers_waiting
from
  {{ source('public_transit', 'station_passenger_stats') }}
