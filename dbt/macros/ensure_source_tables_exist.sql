{% macro ensure_source_tables_exist() %}

  {% set sql %}
    CREATE SCHEMA IF NOT EXISTS public_transit;

    -- These are all tables that are "owned" by Kafka, and are the topic landing tables.
    CREATE TABLE IF NOT EXISTS public_transit.station_passenger_stats (
        station_id INTEGER,
        clock_tick INTEGER,
        total_passengers_in_station INTEGER,
        passengers_boarded_trains INTEGER,
        passengers_entered_station INTEGER,
        passengers_waiting INTEGER,
        trains_at_platform INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(clock_tick, station_id)
    );


    CREATE TABLE IF NOT EXISTS public_transit.runtime_passenger_state (
        clock_tick INTEGER,
        passenger_id INTEGER,
        train_id INTEGER,
        station_id INTEGER,
        stops_seen_so_far INTEGER[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(clock_tick, passenger_id)
    );

    CREATE TABLE IF NOT EXISTS public_transit.runtime_rail_segment_state (
        clock_tick INTEGER,
        segment_id INTEGER,
        trains_present JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(clock_tick, segment_id)
    );

    CREATE TABLE IF NOT EXISTS public_transit.runtime_world_clock_state (
        clock_tick INTEGER,
        year INTEGER,
        day_of_year INTEGER,
        day_of_week VARCHAR(10),
        hour_of_day INTEGER,
        minute INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(clock_tick)
    );

    CREATE TABLE IF NOT EXISTS public_transit.runtime_train_state (
        clock_tick INTEGER,
        train_id INTEGER,
        segment_id INTEGER,
        station_id INTEGER,
        stops_seen_so_far INTEGER[],
        passenger_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(clock_tick, train_id)
    );

    CREATE TABLE IF NOT EXISTS public_transit.runtime_platform_state (
        clock_tick INTEGER,
        station_id INTEGER,
        route_id INTEGER,
        platform_state VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(clock_tick, station_id, route_id)
    );

    CREATE INDEX IF NOT EXISTS idx_train_state_tick_id ON public_transit.runtime_train_state (clock_tick DESC, train_id);
    CREATE INDEX IF NOT EXISTS idx_passenger_state_tick_id ON public_transit.runtime_passenger_state (clock_tick DESC, passenger_id);
    CREATE INDEX IF NOT EXISTS idx_segment_state_tick_id ON public_transit.runtime_rail_segment_state (clock_tick DESC, segment_id);
    CREATE INDEX IF NOT EXISTS idx_station_stats_tick_id ON public_transit.station_passenger_stats (clock_tick DESC, station_id);
    CREATE INDEX IF NOT EXISTS idx_world_clock_tick ON public_transit.runtime_world_clock_state (clock_tick DESC);

  {% endset %}

  {% do run_query(sql) %}
  
{% endmacro %}