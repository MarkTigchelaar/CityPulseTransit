with source as (
    select * from {{ ref('stations') }}
),

renamed as (
    select
        station_id,
        station_name,
        cast(map_x as int) as map_x,
        cast(map_y as int) as map_y
    from source
)

select
    station_id,
    station_name,
    map_x,
    map_y
from renamed
