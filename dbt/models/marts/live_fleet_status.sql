{{ config(materialized='view') }}

with 

-- 1. Get the latest status for every train (Speed, Passenger Count, Station)
latest_train_logs as (
    select distinct on (train_id)
        train_id,
        clock_tick,
        station_id,
        segment_id,
        passenger_count
    from
        {{ ref('runtime_train_state') }}
    order by
        train_id,
        clock_tick
    desc
),

-- 2. Find where trains are by looking at the Rail Segment logs
-- We invert the relationship: Segment -> has Train ID -> implies Train Location
latest_segment_locations as (
    select distinct on (train_id)
        train_id,
        segment_id,
        clock_tick
    from
        {{ ref('runtime_rail_segment_state') }}
    where
        train_id is not null
    order by
        train_id,
        clock_tick
    desc
),

-- 3. Static Reference Data
-- routes as (
--     select
--         route_id,
--         stop_sequence,
--         station_id
--     from
--         {{ ref('routes') }}
-- ),

train_configs as (
    select 
        train_id,
        route_id,
        capacity as max_capacity
    from
        {{ ref('trains') }}
),

train_speed as (
    select
        clock_tick,
        train_speed
    from
        {{ ref('user_adjustable_variables_state')}}
    order by
        clock_tick
    desc
)

-- 4. Merge it all together
select
    t.train_id,
    tc.route_id,
    t.clock_tick,
    t.station_id,
    
    -- This is the Key Change: We pull segment_id from the joined segment log
    s.segment_id, 
    
    ts.train_speed as speed,
    t.passenger_count,
    tc.max_capacity,
    
    -- Calculate Utilization %
    case 
        when tc.max_capacity > 0 then round((t.passenger_count::decimal / tc.max_capacity::decimal) * 100, 1)
        else 0 
    end as utilization_pct,
    
    -- Determine Status
    case 
        when ts.train_speed = 0 and t.station_id is not null then 'Docked'
        when ts.train_speed > 0 then 'In Transit'
        else 'Idle'
    end as status

from latest_train_logs t
-- Join to the segment logs to find the train's location if it's not at a station
left join latest_segment_locations s
on
    t.train_id = s.train_id
and
    t.clock_tick = s.clock_tick
left join train_configs tc
on
    t.train_id = tc.train_id
left join train_speed ts
on
    t.clock_tick = ts.clock_tick