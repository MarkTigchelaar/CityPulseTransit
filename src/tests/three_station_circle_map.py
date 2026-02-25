"""
Three stations connected in a circle A <-> B <-> C <-> A.
Two routes: One Clockwise, One Counter-Clockwise.
"""

from initial_runtime_state import InitialRuntimeState


class ThreeStationCircleMap(InitialRuntimeState):
    def setUp(self):
        super().setUp()

        # Route 101: Clockwise (1 -> 2 -> 3 -> 1)
        # Route 102: Counter-Clockwise (1 -> 3 -> 2 -> 1)
        self.route_config = [
            # Route 101
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 3, "stop_sequence": 3},
            {"route_id": 101, "station_id": 1, "stop_sequence": 4},
            # Route 102
            {"route_id": 102, "station_id": 1, "stop_sequence": 1},
            {"route_id": 102, "station_id": 3, "stop_sequence": 2},
            {"route_id": 102, "station_id": 2, "stop_sequence": 3},
            {"route_id": 102, "station_id": 1, "stop_sequence": 4},
        ]

        self.station_config = [
            {"station_id": 1, "station_name": "Station A"},
            {"station_id": 2, "station_name": "Station B"},
            {"station_id": 3, "station_name": "Station C"},
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
                "station_id": 1,
                "route_id": 102,
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
                "station_id": 2,
                "route_id": 102,
                "platform_state": self._default_platform_state(),
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 101,
                "platform_state": self._default_platform_state(),
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 102,
                "platform_state": self._default_platform_state(),
            },
        ]

        self.segment_config = [
            {
                "segment_id": 12,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 21,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 23,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 32,
                "from_station_id": 3,
                "to_station_id": 2,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 31,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 10.0,
                "speed": 1.0,
            },
            {
                "segment_id": 13,
                "from_station_id": 1,
                "to_station_id": 3,
                "distance_km": 10.0,
                "speed": 1.0,
            },
        ]
