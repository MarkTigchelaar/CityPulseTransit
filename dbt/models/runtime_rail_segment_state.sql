{{ config(materialized='table') }}

select
    segment_id,
    clock_tick,
    train_queuing_order,
    train_id,
    train_position
from
    {{ ref('rail_segment_state') }}
