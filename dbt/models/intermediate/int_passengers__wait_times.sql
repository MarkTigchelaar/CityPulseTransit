{{ config(materialized='view') }}

with passenger_status as (
    select
        passenger_id,
        clock_tick,
        station_id,
        train_id
    from {{ ref('int_passengers__recent_state') }}
),

latest_status as (
    select
        passenger_id,
        station_id,
        train_id,
        row_number() over (partition by passenger_id order by clock_tick desc) as rn
    from passenger_status
),

currently_waiting as (
    select
        passenger_id,
        station_id
    from latest_status
    where rn = 1 and train_id is null and station_id is not null
)

select
    cw.passenger_id,
    max(ps.clock_tick) - min(ps.clock_tick) as wait_time_ticks
from currently_waiting as cw
inner join passenger_status as ps
    on
        cw.passenger_id = ps.passenger_id
        and cw.station_id = ps.station_id
        and ps.train_id is null
group by cw.passenger_id
