{{ config(materialized='view') }}

select 
    station_id,
    station_name,
    total_passengers_in_station,
    passengers_waiting
from {{ ref('int_station_passengers__recent_stats') }}