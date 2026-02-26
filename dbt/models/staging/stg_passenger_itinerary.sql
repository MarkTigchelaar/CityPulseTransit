{{ config(materialized='view') }}

select
    cast(id as int) as id,
    cast(passenger_route_id as int) as passenger_route_id,
    cast(start_arrival_hour as int) as start_arrival_hour,
    cast(arrival_minute as int) as arrival_minute,
    travel_code
from {{ ref('passenger_itinerary') }}
