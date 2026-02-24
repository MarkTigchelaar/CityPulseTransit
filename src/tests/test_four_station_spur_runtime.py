from four_station_spur_map import FourStationSpurMap
from simulation.constants import PlatformState
import unittest


class TestFourStationSpurRuntime(FourStationSpurMap):
    """
    Tests specific to the Junction (Station 3) logic:
    1. Branch Selection (Diverging)
    2. Zipper Merging (Converging)
    """

    def test_branch_selection_diverging(self):
        """
        Scenario: Train at Junction (Stn 3).
        Route 101 goes 3 -> 4 (Spur).
        Route 102 goes 3 -> 2 (Circle).
        Verify trains pick the correct outgoing segment.
        """
        # 1. Setup
        # Train 1 (Route 101) at Stn 3, needs to go to Stn 4.
        # Train 2 (Route 102) at Stn 3, needs to go to Stn 2.
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100},
            {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 100},
        ]

        # Both trains are ready to depart Station 3
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": 3,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [1, 2, 3],
            },  # Next is Stn 4
            {
                "clock_tick": self.clock_tick,
                "train_id": 2,
                "station_id": 3,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [1, 3, 4, 3],
            },  # Next is Stn 2
        ]

        # Configure platforms at Stn 3 to be holding these trains, ready to depart
        self.station_state = [
            # Default others
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

        # 2. Run (Depart Station 3)
        self.run_once()

        # 3. Verify Locations
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

    # def test_zipper_merge_converging(self):
    #     """
    #     Scenario: Two trains arriving at Junction (Stn 3) at the same time.
    #     Train 1 coming from Stn 4 (Spur).
    #     Train 2 coming from Stn 2 (Circle).
    #     Verify one enters, one waits (no collision/crash).
    #     """
    #     # 1. Setup
    #     self.train_config = [
    #         {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100},
    #         {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 100}
    #     ]

    #     # Train 1: In Seg 43 (4->3), 4.9km / 5.0km (Arriving now)
    #     # Train 2: In Seg 23 (2->3), 9.9km / 10.0km (Arriving now)
    #     self.train_state = [
    #         {"clock_tick": self.clock_tick, "train_id": 1, "station_id": None, "segment_id": 43, "position_km": 4.9, "number_of_stops_seen": 3},
    #         {"clock_tick": self.clock_tick, "train_id": 2, "station_id": None, "segment_id": 23, "position_km": 9.9, "number_of_stops_seen": 1}
    #     ]

    #     self.load_system()
    #     self.producer.clear()

    #     # 2. Run (Both attempt arrival)
    #     self.run_once()

    #     # 3. Verify Station State
    #     # Station 3 has platforms for Route 101 and 102.
    #     # Since they are on DIFFERENT routes, they should actually BOTH be able to dock!
    #     # (Unlike a Hub where they share one platform, here they have dedicated platforms).
    #     # So we expect BOTH to arrive.

    #     stn3_events = [e for e in self.producer.get_events("station_state") if e["station_id"] == 3]
    #     latest = stn3_events[-1]

    #     # Check trains at platform
    #     trains_docked = latest["trains_at_platform"]
    #     self.assertIn(101, trains_docked, "Train 1 should have docked at Platform 101")
    #     self.assertIn(102, trains_docked, "Train 2 should have docked at Platform 102")
    #     self.assertEqual(trains_docked[101], 1)
    #     self.assertEqual(trains_docked[102], 2)


if __name__ == "__main__":
    unittest.main()
