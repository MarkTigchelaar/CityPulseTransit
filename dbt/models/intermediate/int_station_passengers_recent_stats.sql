with stats as (
    select * from {{ ref('stg_station_passenger_stats') }}
),

stations as (
    select * from {{ ref('stg_stations') }}
),

current_clock as (
    select * from {{ ref('int_clock_current_state') }}
),

recent_logs as (
    select
        sps.station_id,
        sps.total_passengers_in_station,
        sps.passengers_boarded_trains,
        sps.passengers_entered_station,
        sps.passengers_waiting,
        row_number() over (
            partition by sps.station_id 
            order by sps.clock_tick desc
        ) as rn
    from stats as sps
    inner join current_clock as c on sps.clock_tick >= c.clock_tick - 5
),

final as (
    select
        ps.station_id,
        sn.station_name,
        ps.total_passengers_in_station,
        ps.passengers_boarded_trains,
        ps.passengers_entered_station,
        ps.passengers_waiting
    from recent_logs as ps
    left join stations as sn on ps.station_id = sn.station_id
    where ps.rn = 1
)

select
    station_id,
    station_name,
    total_passengers_in_station,
    passengers_boarded_trains,
    passengers_entered_station,
    passengers_waiting
from final
