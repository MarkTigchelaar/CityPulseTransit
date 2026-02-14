{{ config(materialzed='table') }}

select
    clock_tick,
    day_of_week,
    hour_of_day,
    minute
from
    {{ ref('world_clock_state') }}
