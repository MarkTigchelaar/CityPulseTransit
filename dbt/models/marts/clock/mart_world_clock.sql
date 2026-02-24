{{ config(materialized='view') }}

with
base_clock as (
    select
        wcs.clock_tick,
        wcs.year,
        wcs.day_of_year,
        wcs.hour_of_day,
        wcs.minute,
        make_date(wcs.year, 1, 1) + (wcs.day_of_year - 1) * interval '1 day' as actual_date
    from {{ ref('stg_world_clock_state') }} wcs
    inner join {{ ref('int_clock__current_state') }} lct
        on wcs.clock_tick = lct.clock_tick
)

select
    clock_tick,
    year,
    hour_of_day,
    minute,
    trim(to_char(actual_date, 'Day')) as day_name,
    trim(to_char(actual_date, 'Month')) as month_name,
    cast(extract(day from actual_date) as integer) as day_of_month
from base_clock
