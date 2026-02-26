{{ config(materialized='view') }}

select
    station_id,
    station_name,
    cast(map_x as int) as map_x,
    cast(map_y as int) as map_y
from {{ ref('stations') }}
