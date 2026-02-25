{{ config(materialized='view') }}

with train_positions as (
    select
        train_id,
        route_id,
        distance_from_start_km
    from {{ ref('int_trains__linear_positions') }}
),

route_lengths as (
    select
        route_id,
        max(distance_from_start_km) as total_route_km
    from {{ ref('int_route__topology') }}
    group by route_id
),

ordered_trains as (
    select
        train_id,
        route_id,
        distance_from_start_km,
        lead(distance_from_start_km)
            over (partition by route_id order by distance_from_start_km)
            as next_train_dist,
        lead(train_id)
            over (partition by route_id order by distance_from_start_km)
            as next_train_id,
        first_value(distance_from_start_km)
            over (
                partition by route_id
                order by
                    distance_from_start_km
                rows between unbounded preceding and unbounded following
            )
            as first_train_dist,
        first_value(train_id)
            over (
                partition by route_id
                order by
                    distance_from_start_km
                rows between unbounded preceding and unbounded following
            )
            as first_train_id
    from train_positions
)

select
    o.train_id,
    o.route_id,
    o.distance_from_start_km,
    coalesce(o.next_train_id, o.first_train_id) as train_ahead_id,
    case
        when o.next_train_dist is not null
            then o.next_train_dist - o.distance_from_start_km
        else (r.total_route_km - o.distance_from_start_km) + o.first_train_dist
    end as gap_to_next_train_km
from ordered_trains as o
inner join route_lengths as r
    on o.route_id = r.route_id
