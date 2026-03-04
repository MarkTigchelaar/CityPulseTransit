with topology as (
    select * from {{ ref('int_route_topology') }}
),

final as (
    select
        route_id,
        stop_sequence,
        station_name,
        segment_km,
        distance_from_start_km
    from topology
)

select
    route_id,
    stop_sequence,
    station_name,
    segment_km,
    distance_from_start_km
from final
