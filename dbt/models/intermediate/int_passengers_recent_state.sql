with passenger_state as (
    select * from {{ ref('stg_passenger_state') }}
),

current_clock as (
    select * from {{ ref('int_clock_current_state') }}
),

final as (
    select
        ps.clock_tick,
        ps.passenger_id,
        ps.train_id,
        ps.station_id
    from passenger_state as ps
    inner join current_clock as c on ps.clock_tick >= c.clock_tick - 100
)

select
    clock_tick,
    passenger_id,
    train_id,
    station_id
from final
