{{ config(materialized='table') }}

select
    clock_tick,
    clock_rate,
    train_speed
from
    {{ ref('user_adjustable_variables_state') }}
