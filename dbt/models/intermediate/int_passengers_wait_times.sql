{{ config(materialized='view') }}

with state_transitions as (
    -- Look at the raw chronological history of every passenger
    select
        passenger_id,
        clock_tick as boarding_tick,
        train_id,
        -- Grab the tick and train status from their immediate previous event
        lag(clock_tick) over (partition by passenger_id order by clock_tick) as arrival_tick,
        lag(train_id) over (partition by passenger_id order by clock_tick) as prev_train_id
    from {{ ref('stg_passenger_state') }} 
),

completed_waits as (
    -- Only calculate wait times for passengers who just successfully boarded
    select
        passenger_id,
        (boarding_tick - arrival_tick) as wait_time_ticks
    from state_transitions
    where
        train_id is not null         -- They are now on a train
        and prev_train_id is null    -- They were previously waiting on a platform
        and arrival_tick is not null
)

select
    passenger_id,
    wait_time_ticks
from completed_waits
