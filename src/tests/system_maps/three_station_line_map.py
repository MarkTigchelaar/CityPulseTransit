from tests.initial_states.initial_runtime_state import InitialRuntimeState


class ThreeStationLineMap(InitialRuntimeState):
    def setUp(self):
        super().setUp()

        self.route_config = [
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 3, "stop_sequence": 3},
            {"route_id": 101, "station_id": 2, "stop_sequence": 4},
            {"route_id": 101, "station_id": 1, "stop_sequence": 5},
        ]

        self.station_config = [
            {"station_id": 1, "station_name": "Station 1"},
            {"station_id": 2, "station_name": "Station 2"},
            {"station_id": 3, "station_name": "Station 3"},
        ]

        self.station_state = [
            {
                "clock_tick": self.clock_tick,
                "station_id": 1,
                "route_id": 101,
                "platform_state": self._default_platform_state(),
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 2,
                "route_id": 101,
                "platform_state": self._default_platform_state(),
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 101,
                "platform_state": self._default_platform_state(),
            },
        ]

        self.segment_config = [
            {
                "segment_id": 99,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 100,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 101,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 102,
                "from_station_id": 3,
                "to_station_id": 2,
                "distance_km": 10.0,
                "speed": 1.0,
            },
        ]
