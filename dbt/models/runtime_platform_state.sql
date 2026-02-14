{{ config(materialized='table') }}

select
    station_id,
    clock_tick,
    route_id,
    platform_state
from {{ ref('station_platform_state') }}
