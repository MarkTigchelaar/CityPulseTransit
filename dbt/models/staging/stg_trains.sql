{{ config(materialized='view') }}

select
    cast(train_id as int) as train_id,
    cast(route_id as int) as route_id,
    cast(ordering as int) as ordering,
    cast(capacity as int) as capacity
from {{ ref('trains') }}
