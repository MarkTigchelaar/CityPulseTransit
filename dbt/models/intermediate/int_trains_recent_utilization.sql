with current_state as (
    select * from {{ ref('int_trains_recent_state') }}
),

train_specs as (
    select * from {{ ref('stg_trains') }}
),

calculations as (
    select
        c.train_id,
        c.passenger_count,
        t.capacity,
        (cast(c.passenger_count as numeric) / nullif(t.capacity, 0)) * 100.0 as utilization_pct
    from current_state as c
    left join train_specs as t on c.train_id = t.train_id
),

final as (
    select
        train_id,
        passenger_count,
        capacity,
        round(utilization_pct, 1) as utilization_pct
    from calculations
)

select
    train_id,
    passenger_count,
    capacity,
    utilization_pct
from final
