{% macro ensure_source_tables_exist() %}

  {% set sql %}
    CREATE SCHEMA IF NOT EXISTS public_transit;

    CREATE TABLE IF NOT EXISTS public_transit.station_passenger_stats (
        station_id INTEGER,
        clock_tick INTEGER,
        total_passengers_in_station INTEGER,
        passengers_boarded_trains INTEGER,
        passengers_entered_station INTEGER,
        passengers_waiting INTEGER,
        trains_at_platform INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
  {% endset %}

  {% do run_query(sql) %}
  
{% endmacro %}