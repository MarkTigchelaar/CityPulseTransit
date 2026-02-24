{{ config(materialized='view') }}

with 
station_names as (
  select
    station_id,
    station_name
  from
    {{ ref('stations') }}
),
recent_passenger_logs as (
select
  sps.station_id,
  sps.total_passengers_in_station,
  sps.passengers_boarded_trains,
  sps.passengers_entered_station,
  sps.passengers_waiting,
  row_number() over (partition by sps.station_id order by sps.clock_tick desc) as rn
from {{ ref('stg_station_passenger__stats') }} sps
inner join {{ ref('int_clock__current_state') }} icrs
  on sps.clock_tick >= icrs.clock_tick - 5
)

select
    ps.station_id,
    sn.station_name,
    ps.total_passengers_in_station,
    ps.passengers_boarded_trains,
    ps.passengers_entered_station,
    ps.passengers_waiting
from recent_passenger_logs ps
left join {{ ref('stations') }} sn 
    on ps.station_id = sn.station_id
where ps.rn = 1