{{ config(materialized='view') }}


select
    ps.clock_tick,
    ps.passenger_id,
    ps.train_id,
    ps.station_id
from
    {{ ref('stg_passenger_state') }} as ps
inner join
    {{ ref('int_clock_current_state') }} as lct
    on
        ps.clock_tick >= lct.clock_tick - 100
