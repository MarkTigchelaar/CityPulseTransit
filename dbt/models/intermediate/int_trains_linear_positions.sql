with train_state as (
    select * from {{ ref('int_trains_recent_state') }}
),

train_specs as (
    select * from {{ ref('stg_trains') }}
),

topology as (
    select * from {{ ref('int_route_topology') }}
),

offsets as (
    select * from {{ ref('int_segments_recent_state') }}
    where train_id is not null
),

current_trains as (
    select
        tcs.train_id,
        tcs.status,
        tcs.passenger_count,
        tcs.segment_id,
        tcs.recent_stop_sequence,
        t.route_id
    from train_state as tcs
    inner join train_specs as t on tcs.train_id = t.train_id
),

base_positions as (
    select
        ct.train_id,
        ct.route_id,
        ct.status,
        ct.passenger_count,
        ct.segment_id,
        topo.distance_from_start_km as base_distance_km
    from current_trains as ct
    inner join topology as topo
        on ct.route_id = topo.route_id
        and ct.recent_stop_sequence = topo.stop_sequence
),

final as (
    select
        b.train_id,
        b.route_id,
        b.status,
        b.passenger_count,
        b.base_distance_km + coalesce(o.train_position, 0.0) as distance_from_start_km
    from base_positions as b
    left join offsets as o
        on b.segment_id = o.segment_id
        and b.train_id = o.train_id
)

select
    train_id,
    route_id,
    status,
    passenger_count,
    distance_from_start_km
from final
