with source as (
    select * from {{ ref('rail_segments') }}
),

renamed as (
    select
        cast(segment_id as int) as segment_id,
        cast(from_station_id as int) as from_station_id,
        cast(to_station_id as int) as to_station_id,
        cast(distance_km as int) as distance_km,
        cast(speed as numeric) as speed
    from source
)

select
    segment_id,
    from_station_id,
    to_station_id,
    distance_km,
    speed
from renamed
