{{ config(materialized='view') }}


select
    ps.clock_tick,
    ps.passenger_id,
    ps.train_id,
    ps.station_id
from
    {{ ref('stg_passenger_state') }} ps
join
  {{ ref('int_clock__current_state') }} lct
on
  ps.clock_tick >= lct.clock_tick - 100
