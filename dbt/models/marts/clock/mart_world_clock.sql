with clock_state as (
    select * from {{ ref('stg_world_clock_state') }}
),

current_tick as (
    select * from {{ ref('int_clock_current_state') }}
),

base_calculations as (
    select
        wcs.clock_tick,
        wcs.year,
        wcs.day_of_year,
        wcs.hour_of_day,
        wcs.minute,
        make_date(wcs.year, 1, 1) + (wcs.day_of_year - 1) * interval '1 day' as actual_date
    from clock_state as wcs
    inner join current_tick as lct
        on wcs.clock_tick = lct.clock_tick
),

final as (
    select
        clock_tick,
        year,
        hour_of_day,
        minute,
        trim(to_char(actual_date, 'Day')) as day_name,
        trim(to_char(actual_date, 'Month')) as month_name,
        cast(extract(day from actual_date) as integer) as day_of_month
    from base_calculations
)

select
    clock_tick,
    year,
    hour_of_day,
    minute,
    day_name,
    month_name,
    day_of_month
from final
