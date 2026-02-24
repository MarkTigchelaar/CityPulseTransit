{{ config(materialized='view') }}

with positions as (
    select * from {{ ref('int_trains__linear_positions') }}
),

utilization as (
    select train_id, utilization_pct 
    from {{ ref('int_trains__recent_utilization') }}
)

select
    p.train_id,
    p.route_id,
    p.status,
    p.passenger_count,
    u.utilization_pct,
    p.distance_from_start_km
from positions p
left join utilization u 
    on p.train_id = u.train_id
