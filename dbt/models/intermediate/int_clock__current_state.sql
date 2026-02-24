{{ config(materialized='view') }}

with
latest_clock_tick as (
    select max(clock_tick) as clock_tick from
    {{ ref('stg_world_clock_state') }}
)

select
    wcs.clock_tick,
    wcs.year,
    wcs.day_of_year,
    wcs.day_of_week,
    wcs.hour_of_day,
    wcs.minute
from
   {{ ref('stg_world_clock_state') }} wcs
join
   latest_clock_tick lct
on
  lct.clock_tick = wcs.clock_tick