from four_station_spur_map import FourStationSpurMap
from simulation.platform_state import PlatformState
import unittest


class TestFourStationSpurRuntime(FourStationSpurMap):
    def test_branch_selection_diverging(self):
        # Train 1 (Route 101) at Stn 3, needs to go to Stn 4.
        # Train 2 (Route 102) at Stn 3, needs to go to Stn 2.
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100},
            {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 100},
        ]
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": 3,
                "segment_id": None,
                "stops_seen_so_far": [1, 2, 3],
            },
            {
                "clock_tick": self.clock_tick,
                "train_id": 2,
                "station_id": 3,
                "segment_id": None,
                "stops_seen_so_far": [1, 3, 4, 3],
            },
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
                "platform_state": PlatformState.TrainDeparting.value,
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 102,
                "platform_state": PlatformState.TrainDeparting.value,
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 4,
                "route_id": 101,
                "platform_state": self._default_platform_state(),
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 4,
                "route_id": 102,
                "platform_state": self._default_platform_state(),
            },
        ]

        self.load_system()

        self.run_once()
        train_events = self.producer.get_events("train_state")

        # Train 1 should be in Segment 34 (3->4)
        t1_latest = [e for e in reversed(train_events) if e["train_id"] == 1][0]
        self.assertEqual(
            t1_latest["segment_id"], 34, "Train 1 (Spur Route) should enter Segment 34"
        )

        # Train 2 should be in Segment 32 (3->2)
        self.run_once()
        train_events = self.producer.get_events("train_state")

        t2_latest = next(e for e in reversed(train_events) if e["train_id"] == 2)
        self.assertEqual(
            t2_latest["segment_id"],
            32,
            "Train 2 (Circle Route) should enter Segment 32",
        )

    def test_zipper_merge_converging(self):
        self.segment_state = [
            {
                "clock_tick": self.clock_tick,
                "segment_id": 43,
                "trains_present": [{"id": 1, "position_km": 4.9}],
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 13,
                "trains_present": [{"id": 2, "position_km": 9.9}],
            },
        ]

        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100},
            {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 100},
        ]

        # Train 1: In Seg 43 (4->3), 4.9km / 5.0km (Arriving now)
        # Train 2: In Seg 13 (1->3), 9.9km / 10.0km (Arriving now)
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": None,
                "segment_id": 43,
                "stops_seen_so_far": [1, 2, 3],
            },
            {
                "clock_tick": self.clock_tick,
                "train_id": 2,
                "station_id": None,
                "segment_id": 13,
                "stops_seen_so_far": [1],
            },
        ]

        self.load_system()
        self.producer.clear()
        self.run_once()
        self.run_once()

        train_events = [
            e for e in self.producer.get_events("train_state") if e["clock_tick"] > 1
        ]
        self.assertEqual(len(self.train_config), 2)
        train1_event = [e for e in train_events if e["train_id"] == 1][0]
        train2_event = [e for e in train_events if e["train_id"] == 2][0]

        self.assertEqual(train1_event["station_id"], 3)
        self.assertEqual(train2_event["station_id"], 3)


if __name__ == "__main__":
    unittest.main()
