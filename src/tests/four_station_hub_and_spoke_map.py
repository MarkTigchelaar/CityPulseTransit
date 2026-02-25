from initial_runtime_state import InitialRuntimeState


class FourStationHubAndSpokeMap(InitialRuntimeState):
    def setUp(self):
        super().setUp()

        self.route_config = [
            # Route 101: Hub <-> Spoke A (1-2-1)
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 1, "stop_sequence": 3},
            # Route 102: Hub <-> Spoke B (1-3-1)
            {"route_id": 102, "station_id": 1, "stop_sequence": 1},
            {"route_id": 102, "station_id": 3, "stop_sequence": 2},
            {"route_id": 102, "station_id": 1, "stop_sequence": 3},
            # Route 103: Hub <-> Spoke C (1-4-1)
            {"route_id": 103, "station_id": 1, "stop_sequence": 1},
            {"route_id": 103, "station_id": 4, "stop_sequence": 2},
            {"route_id": 103, "station_id": 1, "stop_sequence": 3},
        ]

        self.station_config = [
            {"station_id": 1, "station_name": "Grand Central Hub"},
            {"station_id": 2, "station_name": "North Spoke"},
            {"station_id": 3, "station_name": "East Spoke"},
            {"station_id": 4, "station_name": "West Spoke"},
        ]

        self.station_state = []

        for route_id in [101, 102, 103]:
            self.station_state.append(
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 1,
                    "route_id": route_id,
                    "platform_state": self._default_platform_state(),
                }
            )

        self.station_state.append(
            {
                "clock_tick": self.clock_tick,
                "station_id": 2,
                "route_id": 101,
                "platform_state": self._default_platform_state(),
            }
        )
        self.station_state.append(
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 102,
                "platform_state": self._default_platform_state(),
            }
        )
        self.station_state.append(
            {
                "clock_tick": self.clock_tick,
                "station_id": 4,
                "route_id": 103,
                "platform_state": self._default_platform_state(),
            }
        )

        self.segment_config = [
            # Spoke 2
            {
                "segment_id": 12,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 1,
                "speed": 1.0,
            },
            {
                "segment_id": 21,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 1,
                "speed": 1.0,
            },
            # Spoke 3
            {
                "segment_id": 13,
                "from_station_id": 1,
                "to_station_id": 3,
                "distance_km": 1,
                "speed": 1.0,
            },
            {
                "segment_id": 31,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 1,
                "speed": 1.0,
            },
            # Spoke 4
            {
                "segment_id": 14,
                "from_station_id": 1,
                "to_station_id": 4,
                "distance_km": 1,
                "speed": 1.0,
            },
            {
                "segment_id": 41,
                "from_station_id": 4,
                "to_station_id": 1,
                "distance_km": 1,
                "speed": 1.0,
            },
        ]
