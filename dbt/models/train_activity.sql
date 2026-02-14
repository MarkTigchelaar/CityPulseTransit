{{ config(materialized='view') }}

with 
movements as (
    -- Now we just read from the one table
    select * from {{ ref('runtime_train_state') }}
),

stations as (
    select * from {{ ref('stations') }}
)

select
    s.station_name,
    m.station_id,
    count(*) as total_visits,
    max(m.clock_tick) as last_seen_tick
from movements m
left join stations s on m.station_id = s.station_id
where m.station_id is not null
group by 1, 2
order by total_visits desc