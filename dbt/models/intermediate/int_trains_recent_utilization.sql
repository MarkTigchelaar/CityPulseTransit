{{ config(materialized='view') }}

with current_state as (
    select * from {{ ref('int_trains_recent_state') }}
),

train_specs as (
    select * from {{ ref('stg_trains') }}
),

safe_calculation as (
    select
        c.train_id,
        c.passenger_count,
        t.capacity,
        -- make it some ridiculus number above 100% if null(so it's obvious, but doesn't crash)
        (
            cast(c.passenger_count as numeric)
            / nullif(t.capacity, 0)
        ) * 100.0 as utilization_pct
    from current_state as c
    left join train_specs as t
        on c.train_id = t.train_id
)

select
    train_id,
    passenger_count,
    capacity,
    round(utilization_pct, 1) as utilization_pct
from safe_calculation
