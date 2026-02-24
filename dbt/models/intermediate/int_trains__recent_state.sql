{{ config(materialized='view') }}

with 
recent_train_logs as (
    select 
        t.train_id,
        t.station_id,
        t.segment_id,
        t.stops_seen_so_far,
        t.passenger_count,
        row_number() over (partition by t.train_id order by t.clock_tick desc) as row_num
    from {{ ref('stg_train_state') }} t
    cross join {{ ref('int_clock__current_state') }} gc
    where t.clock_tick >= gc.clock_tick - 5
)

select 
  train_id,
  station_id,
  segment_id,
  stops_seen_so_far,
  passenger_count,
  
  case 
      when segment_id is not null and station_id is null then 'MOVING'
      when segment_id is null and station_id is not null then 'IN_STATION'
      else 'UNKNOWN' 
  end as status,
  
  greatest(coalesce(array_length(stops_seen_so_far, 1), 0) - 1, 0) as recent_stop_sequence
  
from recent_train_logs
where row_num = 1