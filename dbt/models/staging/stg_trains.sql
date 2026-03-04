with source as (
    select * from {{ ref('trains') }}
),

renamed as (
    select
        cast(train_id as int) as train_id,
        cast(route_id as int) as route_id,
        cast(ordering as int) as ordering,
        cast(capacity as int) as capacity
    from source
)

select
    train_id,
    route_id,
    ordering,
    capacity
from renamed
