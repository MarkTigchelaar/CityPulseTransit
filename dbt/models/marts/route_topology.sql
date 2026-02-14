{{ config(materialized='table') }}

-- Flatten routes to linear distances for visualization
select 
    r.route_id,
    r.stop_sequence,
    r.station_id,
    s.station_name,
    -- This is a simplification: assuming stop_sequence roughly equals distance units
    -- In a real app, you'd sum the segment distances.
    r.stop_sequence * 5.0 as linear_distance_km 
from {{ ref('routes') }} r
join {{ ref('stations') }} s on r.station_id = s.station_id
order by r.route_id, r.stop_sequence