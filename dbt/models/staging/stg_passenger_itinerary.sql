with source as (
    select * from {{ ref('passenger_itinerary') }}
),

renamed as (
    select
        cast(id as int) as id,
        cast(passenger_route_id as int) as passenger_route_id,
        cast(start_arrival_hour as int) as start_arrival_hour,
        cast(arrival_minute as int) as arrival_minute,
        travel_code
    from source
)

select
    id,
    passenger_route_id,
    start_arrival_hour,
    arrival_minute,
    travel_code
from renamed
