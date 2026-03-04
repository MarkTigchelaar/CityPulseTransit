with source as (
    select * from {{ ref('routes') }}
),

renamed as (
    select
        cast(route_id as int) as route_id,
        cast(stop_sequence as int) as stop_sequence,
        cast(station_id as int) as station_id
    from source
)

select
    route_id,
    stop_sequence,
    station_id
from renamed
