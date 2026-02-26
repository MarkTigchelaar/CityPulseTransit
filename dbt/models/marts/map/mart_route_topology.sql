{{ config(materialized='view') }}

select
    route_id,
    stop_sequence,
    station_name,
    segment_km,
    distance_from_start_km
from {{ ref('int_route_topology') }}
