from system_maps.four_station_hub_and_spoke_map import FourStationHubAndSpokeMap
from src.simulation.domain.platform_state import PlatformState
import unittest


class TestFourStationHubRuntime(FourStationHubAndSpokeMap):
    def test_multi_hop_transfer(self):
        self.passenger_itinerary = [
            {
                "id": 1,
                "passenger_route_id": 999,
                "start_arrival_hour": 8,
                "arrival_minute": 1,
                "travel_code": "M",
            }
        ]
        self.passenger_routes = [
            {"route_id": 999, "stop_sequence": 0, "station_id": 2},
            {"route_id": 999, "stop_sequence": 1, "station_id": 1},
            {"route_id": 999, "stop_sequence": 2, "station_id": 3},
            {"route_id": 999, "stop_sequence": 3, "station_id": 1},
            {"route_id": 999, "stop_sequence": 4, "station_id": 4},
        ]
        self.passenger_state = [
            {
                "clock_tick": self.clock_tick,
                "passenger_id": 1,
                "train_id": None,
                "station_id": None,  # Have passenger enter system at first stop on route
                "stops_seen_so_far": [],
            }
        ]

        # Train 1 (Route 101: 2<->1) at Stn 2.
        # Train 2 (Route 102: 3<->1) at Stn 1.
        # Train 3 (Route 103: 4<->1) at Stn 1.
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 1},
            {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 1},
            {"train_id": 3, "route_id": 103, "ordering": 1, "capacity": 1},
        ]

        # Only the train at station 2 is ready for loading, others at station 1 and will leave before passenger arrives
        # This is to create a waiting condition for the passenger to test transfer logic.
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": 2,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [1, 2],
            },
            {
                "clock_tick": self.clock_tick,
                "train_id": 2,
                "station_id": 1,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [1],
            },
            {
                "clock_tick": self.clock_tick,
                "train_id": 3,
                "station_id": 1,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [1],
            },
        ]

        self.segment_state = [
            {
                "clock_tick": self.clock_tick,
                "segment_id": 12,
                "train_queuing_order": 0,
                "train_id": None,
                "trains_present": [],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 21,
                "train_queuing_order": 0,
                "train_id": None,
                "trains_present": [],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 13,
                "train_queuing_order": 0,
                "train_id": None,
                "trains_present": [],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 31,
                "train_queuing_order": 0,
                "train_id": None,
                "trains_present": [],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 41,
                "train_queuing_order": 0,
                "train_id": None,
                "trains_present": [],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 14,
                "train_queuing_order": 0,
                "train_id": None,
                "trains_present": [],
            },
        ]

        for station_state in self.station_state:
            if station_state["station_id"] == 1:
                if station_state["route_id"] == 101:
                    station_state["platform_state"] = PlatformState.Empty.value
                else:
                    station_state["platform_state"] = (
                        PlatformState.MovingPassengers.value
                    )
            if station_state["station_id"] == 2:
                station_state["platform_state"] = PlatformState.MovingPassengers.value

        self.load_system()

        # Confirm passenger did arrive at station 4
        self._run_until_passenger_at_station(passenger_id=1, station_id=4, max_ticks=23)
        p_events = self.producer.get_events("passenger_travelling_state")
        arrivals = [e["station_id"] for e in p_events if e["passenger_id"] == 1]
        stations_seen_last = p_events[-1]["stops_seen_so_far"]
        self.assertIn(2, arrivals, "Must start at Station 2")
        self.assertIn(4, arrivals, "Must end at Station 4")
        self.assertGreaterEqual(
            arrivals.count(1),
            1,
            "Must visit Hub (1) at least twice (Transfer In, Loop Return) but immediately switches trains, so doesn't wait one clock tick",
        )
        self.assertEqual(
            stations_seen_last,
            [2, 1, 3, 1, 4],
            "Jumps to other trains without waiting, but stops seen must show all the stations visited",
        )
        train_events = self.producer.get_events("train_state")

        def check_train_segment_load(train_id, segment_id, min_passengers=1):
            logs = [
                e
                for e in train_events
                if e["train_id"] == train_id and e["segment_id"] == segment_id
            ]
            was_loaded = any(e["passenger_count"] >= min_passengers for e in logs)
            self.assertTrue(
                was_loaded,
                f"Train {train_id} should carry passengers on Segment {segment_id}",
            )

        check_train_segment_load(train_id=1, segment_id=21)
        check_train_segment_load(train_id=2, segment_id=13)
        check_train_segment_load(train_id=2, segment_id=31)
        check_train_segment_load(train_id=3, segment_id=14)

        station_events = self.producer.get_events("station_state")
        hub_logs = [e for e in station_events if e["station_id"] == 1]
        total_hub_boardings = sum(e["passengers_boarded_trains"] for e in hub_logs)

        self.assertGreaterEqual(
            total_hub_boardings,
            2,
            "Hub (Station 1) should process at least 2 boardings",
        )


if __name__ == "__main__":
    unittest.main()
