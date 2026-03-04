with routes as (
    select * from {{ ref('stg_routes') }}
),

stations as (
    select * from {{ ref('stg_stations') }}
),

segments as (
    select * from {{ ref('rail_segments') }}
),

route_stops as (
    select
        r.route_id,
        r.stop_sequence,
        r.station_id,
        s.station_name,
        s.map_x,
        s.map_y,
        lag(r.station_id) over (
            partition by r.route_id
            order by r.stop_sequence
        ) as previous_station_id
    from routes as r
    inner join stations as s on r.station_id = s.station_id
),

segment_lengths as (
    select
        rs.route_id,
        rs.stop_sequence,
        rs.station_name,
        rs.map_x,
        rs.map_y,
        coalesce(seg.distance_km, 0) as segment_km
    from route_stops as rs
    left join segments as seg
        on rs.previous_station_id = seg.from_station_id
        and rs.station_id = seg.to_station_id
),

linear_calculations as (
    select
        route_id,
        stop_sequence,
        station_name,
        map_x,
        map_y,
        segment_km,
        sum(segment_km) over (
            partition by route_id
            order by stop_sequence
            rows between unbounded preceding and current row
        ) as distance_from_start_km
    from segment_lengths
),

final as (
    select
        route_id,
        stop_sequence,
        station_name,
        map_x,
        map_y,
        segment_km,
        distance_from_start_km,
        max(distance_from_start_km) over () as max_system_length_km
    from linear_calculations
)

select
    route_id,
    stop_sequence,
    station_name,
    map_x,
    map_y,
    segment_km,
    distance_from_start_km,
    max_system_length_km
from final
order by route_id, stop_sequence
