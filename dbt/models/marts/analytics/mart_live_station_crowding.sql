with recent_stats as (
    select * from {{ ref('int_station_passengers_recent_stats') }}
),

final as (
    select
        station_id,
        station_name,
        total_passengers_in_station,
        passengers_waiting
    from recent_stats
)

select
    station_id,
    station_name,
    total_passengers_in_station,
    passengers_waiting
from final
