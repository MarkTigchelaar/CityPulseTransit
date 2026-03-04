with seed_data as (
    select * from {{ ref('rail_segment_state') }}
),

live_data as (
    select * from {{ source('public_transit', 'runtime_rail_segment_state') }}
),

unioned as (
    select
        cast(segment_id as integer) as segment_id,
        cast(clock_tick as integer) as clock_tick,
        cast(trains_present as jsonb) as trains_present
    from seed_data

    union all

    select
        cast(segment_id as integer) as segment_id,
        cast(clock_tick as integer) as clock_tick,
        cast(trains_present as jsonb) as trains_present
    from live_data
)

select
    segment_id,
    clock_tick,
    trains_present
from unioned
