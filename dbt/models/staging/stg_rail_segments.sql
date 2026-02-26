{{ config(materialized='view') }}

select
    cast(segment_id as int) as segment_id,
    cast(from_station_id as int) as from_station_id,
    cast(to_station_id as int) as to_station_id,
    cast(distance_km as int) as distance_km,
    cast(speed as numeric) as speed
from {{ ref('rail_segments') }}
