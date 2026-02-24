{{ config(materialized='view') }}

with seed_data as (
    select
        cast(segment_id as integer) as segment_id,
        cast(clock_tick as integer) as clock_tick,
        cast(trains_present as jsonb) as trains_present
    from {{ ref('rail_segment_state') }}
),

live_data as (
    select
        cast(segment_id as integer) as segment_id,
        cast(clock_tick as integer) as clock_tick,
        cast(trains_present as jsonb) as trains_present
    from {{ source('public_transit', 'runtime_rail_segment_state') }}
),

combined_events as (
    select * from seed_data
    union all
    select * from live_data
)

select * from combined_events
