import unittest
from src.simulation.bootstrap.component_loader import ComponentLoader
from tests.data_reader.mock_data_reader import UnittestDataReader
from src.simulation.domain.platform_state import PlatformState
from src.simulation.domain.travel_days import TravelDays
from tests.data_streams.dummy_producer import DummyProducer

DEFAULT_CLOCK_TICK = 0

class InitialLoaderState(unittest.TestCase):
    def setUp(self):
        self.clock_tick = DEFAULT_CLOCK_TICK
        self.producer = DummyProducer()

        self.default_clock = {
            "clock_tick": self.clock_tick,
            "year": 2026,
            "day_of_year": 54, # Feb 23        
            "day_of_week": TravelDays.Monday.value,
            "hour_of_day": 8,
            "minute": 0,
        }

        self.segment_config = [
            {
                "segment_id": 99,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10.0,
                "speed": 10.0
            },
            {
                "segment_id": 100,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 10.0,
                "speed": 10.0
            }
        ]
        self.segment_state = [
            {
                "clock_tick": self.clock_tick,
                "segment_id": 99,
                "train_queuing_order": 0,
                "trains_present": [],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 100,
                "train_queuing_order": 0,
                "trains_present": [],
            }
        ]

        # A simple route (Route 1: Station 1 -> Station 2 -> Station 1)
        self.route_config = [
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 1, "stop_sequence": 3},
        ]

        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100},
            {"train_id": 2, "route_id": 101, "ordering": 2, "capacity": 100},
        ]

        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": 1,
                "segment_id": None,
                "stops_seen_so_far": [1],
            },
            {
                "clock_tick": self.clock_tick,
                "train_id": 2,
                "station_id": 2,
                "stops_seen_so_far": [1],
            },
        ]

        self.station_config = [
            {"station_id": 1, "station_name": "Midway Station"},
            {"station_id": 2, "station_name": "Endpoint Station"},
        ]

        self.station_state = [
            {
                "clock_tick": self.clock_tick,
                "station_id": 1,
                "route_id": 101,
                "platform_state": PlatformState.Empty.value,
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 2,
                "route_id": 101,
                "platform_state": PlatformState.Empty.value,
            },
        ]

        self.passenger_itinerary = [
            {
                "id": 1,
                "passenger_route_id": 101,
                "start_arrival_hour": 8,
                "arrival_minute": 0,
                "travel_code": "MTWRF",
            }
        ]
        self.passenger_routes = [
            {"route_id": 101, "stop_sequence": 0, "station_id": 1},
            {"route_id": 101, "stop_sequence": 1, "station_id": 2}
        ]
        self.passenger_state = [
            {
                "clock_tick": self.clock_tick,
                "passenger_id": 1,
                "train_id": None,
                "station_id": None,
                "stops_seen_so_far": [],
            }
        ]

    def _make_component_loader(self) -> ComponentLoader:
        reader = UnittestDataReader(
            world_clock_config=self.default_clock,
            rail_segment_config=self.segment_config,
            rail_segment_runtime_state=self.segment_state,
            route_config=self.route_config,
            train_config=self.train_config,
            train_runtime_state=self.train_state,
            station_config=self.station_config,
            station_runtime_state=self.station_state,
            passenger_itinerary=self.passenger_itinerary,
            passenger_routes=self.passenger_routes,
            passenger_runtime_state=self.passenger_state,
        )
        return ComponentLoader(reader, self.producer)
    
    def _default_platform_state(self) -> str:
        return PlatformState.Empty.value