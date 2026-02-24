{{ config(materialized='view') }}

select
    train_id,
    route_id,
    train_ahead_id,
    round(cast(gap_to_next_train_km as numeric), 2) as gap_km,
    case
        when gap_to_next_train_km < 0.2 then '🔴 Bunched'
        when gap_to_next_train_km < 0.5 then '🟡 Gapped'
        else '🟢 Optimal'
    end as spacing_health
from {{ ref('int_train__spacing') }}
order by route_id, distance_from_start_km
