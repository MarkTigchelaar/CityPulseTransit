from initial_runtime_state import InitialRuntimeState


class FourStationSpurMap(InitialRuntimeState):
    def setUp(self):
        super().setUp()

        # Route 101: Clockwise Loop visiting Spur (1 -> 2 -> 3 -> 4 -> 3 -> 1)
        # Route 102: Counter-Clockwise Loop visiting Spur (1 -> 3 -> 4 -> 3 -> 2 -> 1)
        self.route_config = [
            # Route 101
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 3, "stop_sequence": 3},
            {"route_id": 101, "station_id": 4, "stop_sequence": 4},
            {"route_id": 101, "station_id": 3, "stop_sequence": 5},
            {"route_id": 101, "station_id": 1, "stop_sequence": 6},
            # Route 102
            {"route_id": 102, "station_id": 1, "stop_sequence": 1},
            {"route_id": 102, "station_id": 3, "stop_sequence": 2},
            {"route_id": 102, "station_id": 4, "stop_sequence": 3},
            {"route_id": 102, "station_id": 3, "stop_sequence": 4},
            {"route_id": 102, "station_id": 2, "stop_sequence": 5},
            {"route_id": 102, "station_id": 1, "stop_sequence": 6},
        ]

        self.station_config = [
            {"station_id": 1, "station_name": "Circle Start"},
            {"station_id": 2, "station_name": "Circle Mid"},
            {"station_id": 3, "station_name": "Junction"},
            {"station_id": 4, "station_name": "Spur End"},
        ]

        self.station_state = []
        for station in self.station_config:
            self.station_state.append(
                {
                    "clock_tick": self.clock_tick,
                    "station_id": station["station_id"],
                    "route_id": 101,
                    "platform_state": self._default_platform_state(),
                }
            )
            self.station_state.append(
                {
                    "clock_tick": self.clock_tick,
                    "station_id": station["station_id"],
                    "route_id": 102,
                    "platform_state": self._default_platform_state(),
                }
            )

        self.segment_config = [
            # Circle Segments (1-2, 2-3, 3-1)
            {
                "segment_id": 12,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 21,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 23,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 32,
                "from_station_id": 3,
                "to_station_id": 2,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 31,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 13,
                "from_station_id": 1,
                "to_station_id": 3,
                "distance_km": 10,
                "speed": 1.0,
            },
            # Spur Segments (3-4)
            {
                "segment_id": 34,
                "from_station_id": 3,
                "to_station_id": 4,
                "distance_km": 5,
                "speed": 1.0,
            },
            {
                "segment_id": 43,
                "from_station_id": 4,
                "to_station_id": 3,
                "distance_km": 5,
                "speed": 1.0,
            },
        ]
