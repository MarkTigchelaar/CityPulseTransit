{{ config(materialized='view') }}

select
    cast(route_id as int) as route_id,
    cast(stop_sequence as int) as stop_sequence,
    cast(station_id as int) as station_id
from {{ ref('routes') }}
