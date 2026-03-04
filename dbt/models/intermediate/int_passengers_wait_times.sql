with passenger_state as (
    select * from {{ ref('stg_passenger_state') }}
),

state_transitions as (
    select
        passenger_id,
        clock_tick as boarding_tick,
        train_id,
        lag(clock_tick) over (
            partition by passenger_id 
            order by clock_tick
        ) as arrival_tick,
        lag(train_id) over (
            partition by passenger_id 
            order by clock_tick
        ) as prev_train_id
    from passenger_state
),

completed_waits as (
    select
        passenger_id,
        (boarding_tick - arrival_tick) as wait_time_ticks
    from state_transitions
    where
        train_id is not null
        and prev_train_id is null
        and arrival_tick is not null
)

select
    passenger_id,
    wait_time_ticks
from completed_waits
