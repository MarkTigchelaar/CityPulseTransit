{{ config(materialized='view') }}

with stats as (
    select
        coalesce(max(wait_time_ticks), 0) as max_wait,
        coalesce(min(wait_time_ticks), 0) as min_wait,
        coalesce(round(avg(wait_time_ticks), 1), 0) as avg_wait
    from {{ ref('int_passengers__wait_times') }}
)

-- Unpivot the columns into rows so Altair can consume it instantly
select 'Max' as metric, max_wait as wait_time from stats
union all
select 'Avg' as metric, avg_wait from stats
union all
select 'Min' as metric, min_wait from stats
