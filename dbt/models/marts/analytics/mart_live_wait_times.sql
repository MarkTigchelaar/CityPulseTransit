with wait_times as (
    select * from {{ ref('int_passengers_wait_times') }}
),

stats as (
    select
        coalesce(max(wait_time_ticks), 0) as max_wait,
        coalesce(min(wait_time_ticks), 0) as min_wait,
        coalesce(round(avg(wait_time_ticks), 1), 0) as avg_wait
    from wait_times
),

final as (
    select
        'Max' as metric,
        max_wait as wait_time
    from stats
    
    union all
    
    select
        'Avg' as metric,
        avg_wait
    from stats
    
    union all
    
    select
        'Min' as metric,
        min_wait
    from stats
)

select
    metric,
    wait_time
from final
