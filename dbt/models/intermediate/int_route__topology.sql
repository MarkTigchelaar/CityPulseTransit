{{ config(materialized='view') }}

with route_stops as (
    select
        r.route_id,
        r.stop_sequence,
        r.station_id,
        s.station_name,
        lag(r.station_id) over (
            partition by r.route_id
            order by r.stop_sequence
        ) as previous_station_id
    from {{ ref('routes') }} as r
    inner join {{ ref('stations') }} as s
        on r.station_id = s.station_id
),

segment_lengths as (
    select
        rs.route_id,
        rs.stop_sequence,
        rs.station_name,
        coalesce(seg.distance_km, 0) as segment_km
    from route_stops as rs
    left join {{ ref('rail_segments') }} as seg
        on
            rs.previous_station_id = seg.from_station_id
            and rs.station_id = seg.to_station_id
),

linear_coordinates as (
    select
        route_id,
        stop_sequence,
        station_name,
        segment_km,
        sum(segment_km) over (
            partition by route_id
            order by stop_sequence
            rows between unbounded preceding and current row
        ) as distance_from_start_km
    from segment_lengths
)

select
    route_id,
    stop_sequence,
    station_name,
    segment_km,
    distance_from_start_km,
    -- Dont collapse all rows down
    max(distance_from_start_km) over (/* linear_coordinates */) as max_system_length_km
from linear_coordinates
order by route_id, stop_sequence
