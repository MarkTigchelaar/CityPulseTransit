from two_station_line_map import TwoStationLineMap
from simulation.constants import PlatformState
import unittest


class TestTwoStationRuntime(TwoStationLineMap):
    """
    Runtime logic tests for a 2-station system using the MemoryProducer.
    """

    def test_train_movement_no_passengers(self):
        """
        Scenario: 1 Train, 0 Passengers.
        Train starts in Segment 99 (1 -> 2) close to arrival.
        Verifies arrival at Station 2.
        This demonstrates the logging of trains is accurate as they move through rail segments
        and into stations.
        """

        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100}
        ]
        # Place train 9.0km along 10km segment (1km left)
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [1],
            }
        ]
        self.segment_state[0].update(
            {"trains_present": [{"id": 1, "position_km": 9.0}]}
        )
        self.passenger_itinerary = []
        self.passenger_state = []

        self.load_system()

        self.run_once()

        train_events = self.producer.get_events("train_state")

        self.assertTrue(
            len(train_events) == 1, "Should have train state events after running once"
        )
        self.assertTrue(train_events[0]["clock_tick"] == 1)
        self.assertTrue(train_events[0]["train_id"] == 1)
        self.assertTrue(train_events[0]["station_id"] is None)
        self.assertTrue(train_events[0]["segment_id"] == 99)

        self.run_once()

        self.assertTrue(
            len(train_events) == 2,
            "Should have train state from arriving at station two",
        )
        arrival = train_events[-1]
        self.assertTrue(arrival["station_id"] == 2)
        self.assertTrue(arrival["segment_id"] is None)
        station_events = self.producer.get_events("station_state")
        self.assertTrue(len(station_events) == 4, "2 clock ticks, 2 stations")

        platform_events = self.producer.get_events("platform_state")
        station_two_platform_tick_two = [
            plat
            for plat in platform_events
            if plat["clock_tick"] == 2 and plat["station_id"] == 2
        ][0]

        self.assertTrue(
            station_two_platform_tick_two["platform_state"]
            == PlatformState.MovingPassengers.value
        )

    def test_single_passenger_flow(self):
        """
        Scenario: 1 Train, 1 Passenger.
        Passenger at Station 2, wants to go to Station 1.
        Train arrives Station 2, Passenger boards.
        """
        # 1. Setup
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100}
        ]
        # Train arriving at Station 2 (Seg 99, 9.5km)
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [1],
            }
        ]

        self.segment_state[0]["trains_present"].append({"id": 1, "position_km": 9.5})

        # Passenger at Station 2, waiting for Route 101 (to go to Stn 1)
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
            {"route_id": 101, "stop_sequence": 0, "station_id": 2},
            {"route_id": 101, "stop_sequence": 1, "station_id": 1},
        ]
        self.passenger_state = [
            {
                "clock_tick": self.clock_tick,
                "passenger_id": 1,
                "train_id": None,
                "station_id": 2,
                "stops_seen_so_far": [2],
            }
        ]

        self.load_system()

        # 2. Verify Initial State (Passenger waiting)
        self.run_once()  # Tick 1

        station_events = self.producer.get_events("station_state")
        stn2_events = [e for e in station_events if e["station_id"] == 2]
        self.assertTrue(len(stn2_events) > 0)
        self.assertEqual(stn2_events[-1]["passengers_waiting"], 1)

        self.run_once()
        stn2_events = [
            e for e in self.producer.get_events("station_state") if e["station_id"] == 2
        ]
        boarded = False
        if stn2_events and stn2_events[-1]["passengers_boarded_trains"] == 1:
            boarded = True

        self.assertFalse(
            boarded,
            "Passenger should not have boarded the train, train arrived outside station after station state logged",
        )

        self.run_once()
        stn2_events = [
            e for e in self.producer.get_events("station_state") if e["station_id"] == 2
        ]
        self.assertEqual(
            stn2_events[-1]["passengers_boarded_trains"],
            1,
            "Passenger should have boarded the train",
        )
        self.assertEqual(
            stn2_events[-1]["passengers_waiting"],
            0,
            "Passenger should no longer be waiting at the station",
        )

    def test_passenger_alighting(self):
        """
        Scenario: Passenger is ON the train. Train arrives at destination.
        Verify Passenger leaves train and logs 'departing' event.
        """
        # 1. Setup
        # Route 101: 1 -> 2 -> 1.
        # Train 1 is currently at Station 1 (Start), but let's say it's about to leave for 2.
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100}
        ]

        # We manually place a passenger ON the train.
        # They want to go to Station 2.
        self.passenger_itinerary = [
            {
                "id": 1,
                "passenger_route_id": 101,
                "start_arrival_hour": 8,
                "arrival_minute": 0,
                "travel_code": "MTWRF",
            }
        ]

        # We need to hack the initial state to put the passenger IN the train
        # The loader supports `train_id` in passenger_runtime_state
        self.passenger_state = [
            {
                "clock_tick": self.clock_tick,
                "passenger_id": 1,
                "train_id": 1,  # <--- Inside Train 1
                "station_id": None,
                "stops_seen_so_far": [1],  # Seen Stn 1, headed to Stn 2
            }
        ]

        self.passenger_routes = [
            {"route_id": 101, "stop_sequence": 0, "station_id": 1},
            {"route_id": 101, "stop_sequence": 1, "station_id": 2},
        ]

        # Train is in segment 99 (1->2), arriving at 2
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [1],
            }
        ]

        self.segment_state[0]["trains_present"].append({"id": 1, "position_km": 9.5})

        self.load_system()

        # 2. Run (Arrive OUTSIDE of Station 2)
        self.run_once()
        self.run_once()

        train_events = self.producer.get_events("train_state")
        self.assertEqual(
            train_events[-1]["passenger_count"],
            1,
            "Train should have one passenger when arriving",
        )

        self.run_once()

        train_events = self.producer.get_events("train_state")
        self.assertEqual(
            train_events[-1]["passenger_count"],
            0,
            "Train should be empty when managing passengers",
        )

        station_events = self.producer.get_events("station_state")
        stn2_events = [e for e in station_events if e["station_id"] == 2]
        self.assertEqual(
            stn2_events[-1]["passengers_boarded_trains"],
            0,
            "No passengers should board, passenger is alighting",
        )
        self.assertEqual(
            stn2_events[-1]["passengers_entered_station"],
            1,
            "One passenger should have exited train, and entered station",
        )

        # # Check Passenger Log (Travelling State)
        # # Passenger logs "departing" when they leave the station/system
        pass_events = self.producer.get_events("passenger_travelling_state")

        # Passengers can enter a station and depart from it in the same go, if they are not waiting for a train.
        self.assertEqual(pass_events[0]["train_id"], 1)
        self.assertEqual(pass_events[1]["train_id"], None)

    def test_train_capacity_limits(self):
        """
        Scenario: 1 Train (Cap 10), 1 Station with 20 Passengers.
        Verify only 10 board, 10 remain waiting.
        """
        # 1. Setup
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 10}
        ]
        # Train arriving Station 2
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [1],
            }
        ]
        self.segment_state[0]["trains_present"].append({"id": 1, "position_km": 9.9})

        # 20 Passengers at Station 2
        self.passenger_itinerary = []
        self.passenger_state = []
        self.passenger_routes = [
            {"route_id": 101, "stop_sequence": 0, "station_id": 2},
            {"route_id": 101, "stop_sequence": 1, "station_id": 1},
        ]

        for i in range(20):
            self.passenger_itinerary.append(
                {
                    "id": i + 1,
                    "passenger_route_id": 101,
                    "start_arrival_hour": 8,
                    "arrival_minute": 0,
                    "travel_code": "MTWRF",
                }
            )
            self.passenger_state.append(
                {
                    "clock_tick": self.clock_tick,
                    "passenger_id": i + 1,
                    "train_id": None,
                    "station_id": 2,
                    "stops_seen_so_far": [2],
                }
            )

        self.load_system()

        # Train movement:
        self.run_once()  # Get to end of segment
        self.run_once()  # Arrive
        self.run_once()  # Board

        stn2_events = [
            e for e in self.producer.get_events("station_state") if e["station_id"] == 2
        ]
        latest = stn2_events[-1]

        self.assertEqual(
            latest["passengers_boarded_trains"],
            10,
            "Should board exactly capacity (10)",
        )
        self.assertEqual(latest["passengers_waiting"], 10, "Should leave 10 waiting")
        self.run_once()  # depart, so log state

        train_events = self.producer.get_events("train_state")
        self.assertEqual(train_events[-1]["passenger_count"], 10)

    def test_two_trains_passing_opposite_routes(self):
        """
        Scenario: 2 Trains, 2 Stations, 2x Capacity Passengers, Opposite Routes.
        """
        # 1. Setup Route 102 (Counter Loop)
        self.route_config.extend(
            [
                {"route_id": 102, "station_id": 2, "stop_sequence": 1},
                {"route_id": 102, "station_id": 1, "stop_sequence": 2},
                {"route_id": 102, "station_id": 2, "stop_sequence": 3},
            ]
        )

        self.station_state.extend(
            [
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 1,
                    "route_id": 102,
                    "platform_state": self._default_platform_state(),
                },
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 2,
                    "route_id": 102,
                    "platform_state": self._default_platform_state(),
                },
            ]
        )

        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 10},
            {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 10},
        ]

        self.train_state = [
            # Train 1 (1->2) in Seg 99, arriving Stn 2
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [1],
            },
            # Train 2 (2->1) in Seg 100, arriving Stn 1
            {
                "clock_tick": self.clock_tick,
                "train_id": 2,
                "station_id": None,
                "segment_id": 100,
                "stops_seen_so_far": [2],
            },
        ]
        self.segment_state[0]["trains_present"].append({"id": 1, "position_km": 9.0})
        self.segment_state[1]["trains_present"].append({"id": 2, "position_km": 9.0})

        self.passenger_itinerary = []
        self.passenger_state = []
        self.passenger_routes = []

        # 20 Pass at Stn 2 wanting Route 101 (to 1)
        p_route_101 = [
            {"route_id": 101, "stop_sequence": 0, "station_id": 2},
            {"route_id": 101, "stop_sequence": 1, "station_id": 1},
        ]
        self.passenger_routes.extend(p_route_101)
        for i in range(20):
            self.passenger_itinerary.append(
                {
                    "id": i + 1,
                    "passenger_route_id": 101,
                    "start_arrival_hour": 8,
                    "arrival_minute": 0,
                    "travel_code": "MTWRF",
                }
            )
            self.passenger_state.append(
                {
                    "clock_tick": self.clock_tick,
                    "passenger_id": i + 1,
                    "train_id": None,
                    "station_id": 2,
                    "stops_seen_so_far": [2],
                }
            )

        # 20 Pass at Stn 1 wanting Route 102 (to 2)
        p_route_102 = [
            {"route_id": 102, "stop_sequence": 0, "station_id": 1},
            {"route_id": 102, "stop_sequence": 1, "station_id": 2},
        ]
        self.passenger_routes.extend(p_route_102)
        for i in range(20, 40):
            self.passenger_itinerary.append(
                {
                    "id": i + 1,
                    "passenger_route_id": 102,
                    "start_arrival_hour": 8,
                    "arrival_minute": 0,
                    "travel_code": "MTWRF",
                }
            )
            self.passenger_state.append(
                {
                    "clock_tick": self.clock_tick,
                    "passenger_id": i + 1,
                    "train_id": None,
                    "station_id": 1,
                    "stops_seen_so_far": [1],
                }
            )

        self.load_system()

        # 2. Run (Both trains arrive and board)
        self.run_once()  # Get to end of segments
        self.run_once()  # Arrive at stations
        self.run_once()  # Board passengers, log station state

        # Verify Stn 1 (Train 2 picked up 10)
        stn1_events = [
            e for e in self.producer.get_events("station_state") if e["station_id"] == 1
        ]
        self.assertEqual(stn1_events[-1]["passengers_boarded_trains"], 10)

        # Verify Stn 2 (Train 1 picked up 10)
        stn2_events = [
            e for e in self.producer.get_events("station_state") if e["station_id"] == 2
        ]
        self.assertEqual(stn2_events[-1]["passengers_boarded_trains"], 10)

    def test_route_looping_reset(self):
        """
        Scenario: Train completes the full route sequence (1->2->1).
        Verify it continues to Station 2 again (starts over).
        """
        # 1. Setup
        # Route 101: 1 -> 2 -> 1.
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100}
        ]

        # Train is at Station 1 (The END of the route sequence)
        # stops_seen = 3 (means it visited 1, 2, and now 1 again).
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": 1,  # At station
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [1, 2, 1],  # Full route seen
            }
        ]

        # Ensure Station 1 has platform ready for departure
        self.station_state = [
            {
                "clock_tick": self.clock_tick,
                "station_id": 1,
                "route_id": 101,
                "platform_state": PlatformState.TrainDeparting.value,
            },
            {
                "clock_tick": self.clock_tick,
                "station_id": 2,
                "route_id": 101,
                "platform_state": PlatformState.Empty.value,
            },
        ]

        self.load_system()
        self.producer.clear()

        # 2. Run (Depart Station 1)
        # It should enter Segment 99 (1->2)
        self.run_once()

        # 3. Verify it is in Segment 99
        train_events = self.producer.get_events("train_state")
        latest = train_events[-1]

        self.assertEqual(
            latest["segment_id"],
            99,
            "Train should restart route and enter Segment 99 (1->2)",
        )
        self.assertEqual(
            latest["stops_seen_so_far"],
            [1],
            "Stops seen should reset to 1 (Station 1 visited, en route to 2)",
        )


if __name__ == "__main__":
    unittest.main()
