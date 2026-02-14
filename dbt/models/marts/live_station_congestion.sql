{{ config(materialized='view') }}

with latest_stats as (
    select distinct on (station_id)
        station_id,
        clock_tick,
        total_passengers_in_station,
        passengers_boarded_trains,
        passengers_entered_station,
        passengers_waiting,
        trains_at_platform
    from {{ source('public_transit', 'station_passenger_stats') }}
    order by station_id, clock_tick desc
),

stations as (
    select * from {{ ref('stations') }}
)

select
    s.station_name,
    l.station_id,
    l.clock_tick,
    l.total_passengers_in_station,
    l.passengers_boarded_trains,
    l.passengers_entered_station,
    l.passengers_waiting,
    l.trains_at_platform
from latest_stats l
left join stations s on l.station_id = s.station_id
order by l.total_passengers_in_station desc