from initial_runtime_state import InitialRuntimeState


class TwoStationLineMap(InitialRuntimeState):
    def setUp(self):
        super().setUp()


        self.station_config = [
            {"station_id": 1, "station_name": "Station 1"},
            {"station_id": 2, "station_name": "Station 2"},
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
        ]

