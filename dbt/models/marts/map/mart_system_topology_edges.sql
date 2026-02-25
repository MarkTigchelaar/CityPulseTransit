{{ config(materialized='view') }}

with route_sequence as (
    select
        route_id,
        stop_sequence,
        station_name,
        lead(station_name) over (partition by route_id order by stop_sequence) as next_station_name
    from {{ ref('int_route__topology') }}
)

select
    route_id,
    station_name,
    next_station_name
from route_sequence
where next_station_name is not null
