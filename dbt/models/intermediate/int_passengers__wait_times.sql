{{ config(materialized='view') }}

with passenger_status as (
    -- Now querying the bounded sliding window instead of the raw history
    select
        passenger_id,
        clock_tick,
        station_id,
        train_id
    from {{ ref('int_passengers__recent_state') }}
),

latest_status as (
    -- Find the absolute latest known state of every passenger within the recent window
    select 
        passenger_id, 
        station_id, 
        train_id,
        row_number() over (partition by passenger_id order by clock_tick desc) as rn
    from passenger_status
),

currently_waiting as (
    -- Filter down to ONLY passengers who are currently at a station right now
    select passenger_id, station_id
    from latest_status
    where rn = 1 and train_id is null and station_id is not null
)

select
    cw.passenger_id,
    -- Calculate wait time restricted to the sliding window
    max(ps.clock_tick) - min(ps.clock_tick) as wait_time_ticks
from currently_waiting cw
join passenger_status ps 
    on cw.passenger_id = ps.passenger_id 
    and cw.station_id = ps.station_id
    and ps.train_id is null
group by cw.passenger_id
