{{ config(materialized='view') }}

with train_metrics as (
    select 
        coalesce(sum(passenger_count), 0) as total_passengers_riding,
        coalesce(avg(utilization_pct), 0.0) as avg_network_utilization_pct,
        count(train_id) as active_trains
    from {{ ref('mart_live_train_positions') }}
),

station_metrics as (
    select 
        coalesce(sum(total_passengers_in_station), 0) as total_passengers_in_stations,
        coalesce(sum(passengers_waiting), 0) as total_passengers_waiting
    from {{ ref('mart_live_station_crowding') }}
)

select
    t.total_passengers_riding + s.total_passengers_in_stations as total_passengers_in_system,
    t.total_passengers_riding,
    s.total_passengers_waiting,
    round(cast(t.avg_network_utilization_pct as numeric), 1) as avg_network_utilization_pct,
    t.active_trains
from train_metrics t
cross join station_metrics s