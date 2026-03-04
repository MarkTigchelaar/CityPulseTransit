with positions as (
    select * from {{ ref('int_trains_linear_positions') }}
),

utilization as (
    select * from {{ ref('int_trains_recent_utilization') }}
),

joined as (
    select
        p.train_id,
        p.route_id,
        p.status,
        p.passenger_count,
        u.utilization_pct,
        p.distance_from_start_km
    from positions as p
    left join utilization as u
        on p.train_id = u.train_id
)

select
    train_id,
    route_id,
    status,
    passenger_count,
    utilization_pct,
    distance_from_start_km
from joined
