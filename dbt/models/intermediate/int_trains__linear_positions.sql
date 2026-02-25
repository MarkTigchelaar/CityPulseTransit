{{ config(materialized='view') }}

with current_trains as (
    select
        tcs.train_id,
        tcs.status,
        tcs.passenger_count,
        tcs.segment_id,
        tcs.recent_stop_sequence,
        t.route_id
    from {{ ref('int_trains__recent_state') }} as tcs
    inner join {{ ref('trains') }} as t
        on tcs.train_id = t.train_id
),

train_topology_base as (
    select
        ct.train_id,
        ct.route_id,
        ct.status,
        ct.passenger_count,
        ct.segment_id,
        topo.distance_from_start_km as base_distance_km
    from current_trains as ct
    inner join {{ ref('int_route__topology') }} as topo
        on
            ct.route_id = topo.route_id
            and ct.recent_stop_sequence = topo.stop_sequence
),

train_offsets as (
    select
        segment_id,
        train_id,
        train_position
    from {{ ref('int_segments__recent_state') }}
    where train_id is not null
)

select
    base.train_id,
    base.route_id,
    base.status,
    base.passenger_count,
    base.base_distance_km + coalesce(ofs.train_position, 0.0) as distance_from_start_km
from train_topology_base as base
left join train_offsets as ofs
    on
        base.segment_id = ofs.segment_id
        and base.train_id = ofs.train_id
