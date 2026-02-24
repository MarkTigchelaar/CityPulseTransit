import unittest
from simulation.constants import PlatformState, TravelDays
from simulation.component_loader import StateLoadingError, ConfigurationError
from initial_loader_state import InitialLoaderState

"""
    All of the unit and integration tests
    were made with the help of Gemini Pro.
    The inheritance structure was all me though.
"""


class TestComponentLoader(InitialLoaderState):

    def test_load_world_clock(self):
        loader = self._make_component_loader()
        loader._load_world_clock()
        clock = loader.get_world_clock()
        self.assertEqual(clock.clock_tick, self.clock_tick)
        self.assertEqual(clock.day_of_week, TravelDays.Monday)

    def test_load_passenger_starts_in_train(self):
        """
        Verifies that a passenger assigned to a train in the runtime state
        is correctly loaded into that train's passenger list.
        """
        self.passenger_state[0].update(
            {
                "train_id": 1,
                "station_id": None,  # Cannot be in two places at once
                "stops_seen_so_far": [1],
            }
        )

        loader = self._make_component_loader()
        loader.load_system_components()

        trains = loader.get_trains()
        target_train = next(t for t in trains if t.id == 1)
        other_trains = [t for t in trains if t.id != 1]

        # Check if passenger is in the train's internal dictionary
        self.assertIn(
            1, target_train.passengers, "Passenger 1 should be inside Train 1"
        )
        for train in other_trains:
            self.assertNotIn(
                1, train.passengers, "Passenger 1 should be inside Train 1"
            )

        # Verify the passenger object state
        passenger = target_train.passengers[1]
        self.assertTrue(
            passenger.is_travelling, "Passenger should be marked as travelling"
        )
        self.assertEqual(passenger.station_ids_visited, [1])

        stations = loader.get_stations()
        for station_id in stations:
            target_station = stations[station_id]

            passenger_ids_in_station = [p.id for p in target_station.passengers]
            self.assertNotIn(
                1,
                passenger_ids_in_station,
                "Passenger 1 should be inside train, not in station",
            )

    def test_load_passenger_starts_in_station(self):
        """
        Verifies that a passenger assigned to a station in the runtime state
        is correctly loaded into that station's passenger list.
        """
        # 1. Update state: Force Passenger 1 to be waiting at Station 1
        self.passenger_state[0].update(
            {
                "train_id": None,  # Not on a train
                "station_id": 1,  # Waiting at Station 1
                "stops_seen_so_far": [],
            }
        )

        loader = self._make_component_loader()
        loader.load_system_components()

        stations = loader.get_stations()
        target_station = stations[1]

        passenger_ids_in_station = [p.id for p in target_station.passengers]
        self.assertIn(
            1, passenger_ids_in_station, "Passenger 1 should be inside Station 1"
        )

        for train in loader.get_trains():
            self.assertNotIn(1, train.passengers)

    def test_load_passengers_raises_error_missing_route_definition(self):
        """
        Verifies that if a passenger's itinerary references a route_id
        that is not defined in the passenger_routes file, the loader raises a KeyError.
        """
        # 1. Setup: Passenger references Route 999
        self.passenger_itinerary.append(
            {
                "id": 1,
                "passenger_route_id": 999,  # This route does not exist in self.passenger_routes
                "start_arrival_hour": 8,
                "arrival_minute": 0,
                "travel_code": "12345",
            }
        )

        # Ensure runtime state exists so we don't fail on the wrong error
        self.passenger_state.append(
            {
                "passenger_id": 1,
                "clock_tick": self.clock_tick,
                "train_id": None,
                "station_id": 1,
                "stops_seen_so_far": [],
            }
        )

        loader = self._make_component_loader()
        loader._load_world_clock()

        # 2. Execution & Assertion
        # Fails when trying to look up route 999 in passenger_routes_lookup
        with self.assertRaises(ConfigurationError):
            loader._load_passengers()

    def test_load_passengers_raises_error_missing_runtime_state(self):
        """
        Verifies that if a passenger exists in the itinerary (static data)
        but has no corresponding row in the runtime state (dynamic data)
        for the current clock tick, the loader raises an IndexError.
        """
        self.passenger_state[0].update({"passenger_id": 2})

        loader = self._make_component_loader()
        loader._load_world_clock()

        with self.assertRaises(StateLoadingError):
            loader._load_passengers()

    def test_load_passengers_raises_error_invalid_travel_days_code(self):
        """
        Verifies that if a passenger has a travel code that is not a valid
        TravelDays enum value (e.g., 'Z'), the loader raises a ValueError.
        """

        # 1. Setup: Invalid Travel Code 'Z'
        self.passenger_itinerary.append(
            {
                "id": 1,
                "passenger_route_id": 101,
                "start_arrival_hour": 8,
                "arrival_minute": 0,
                "travel_code": "Z",
            }
        )

        self.passenger_state.append(
            {
                "passenger_id": 1,
                "clock_tick": self.clock_tick,
                "train_id": None,
                "station_id": 1,
                "stops_seen_so_far": [],
            }
        )

        loader = self._make_component_loader()
        loader._load_world_clock()

        # Fails inside TravelPlan constructor -> TravelDays.from_code
        with self.assertRaises(ConfigurationError):
            loader._load_passengers()

    def test_load_trains_correctly_assigns_attributes(self):
        self.train_state[0].update({"stops_seen_so_far": [1, 2]})
        loader = self._make_component_loader()
        loader.load_system_components()

        trains = loader.get_trains()
        t1 = next(t for t in trains if t.id == 1)
        t2 = next(t for t in trains if t.id == 2)
        # very important this loads correctly.
        # routes are compared to this, and when equal that is
        # the completion of the route. Passegners get off trains and leave
        # trains repeat from beginging of route.
        self.assertEqual(
            t1.station_ids_visited, [1, 2], "Train 1 should have 2 stops seen"
        )
        self.assertEqual(
            t2.station_ids_visited, [1], "Train 2 should have 1 stops seen"
        )

    def test_load_trains_raises_error_missing_route_definition(self):
        """
        Verifies that if a train references a route_id that is not defined
        in the routes file, the loader raises a StateLoadingError.
        """
        # 1. Setup: Train 99 references Route 999 (which doesn't exist)
        self.train_config.append(
            {
                "train_id": 99,
                "route_id": 999,  # Invalid Route ID
                "ordering": 1,
                "capacity": 100,
            }
        )

        # We must add runtime state for this train so it doesn't fail
        # on the "Missing Runtime State" check first.
        self.train_state.append(
            {
                "clock_tick": self.clock_tick,
                "train_id": 99,
                "station_id": 1,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [],
            }
        )

        loader = self._make_component_loader()
        loader._load_world_clock()

        # 2. Execution & Assertion
        # Fails when trying to look up 'routes[999]' inside _load_trains
        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_trains_raises_error_missing_runtime_state(self):
        """
        Verifies that if a train exists in the configuration but has no
        corresponding row in the runtime state (train_state.csv) for the
        current clock tick, it raises an IndexError (or StateLoadingError).
        """
        # 1. Setup: Add Train 99 to config...
        self.train_config.append(
            {"train_id": 99, "route_id": 101, "ordering": 1, "capacity": 100}
        )

        # ...BUT intentionally do NOT add it to self.train_state.

        loader = self._make_component_loader()
        loader._load_world_clock()

        # 2. Execution & Assertion
        # Fails at .iloc[0] when filtering state for this train_id
        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_trains_raises_error_invalid_stops_seen_count(self):
        """
        Verifies that the Train constructor raises an exception if the
        loaded 'stops_seen_so_far' is greater than the total stops on the route.
        """
        # 1. Setup: Train 1 is on Route 101 (which has 2 stops).
        # We update its state to claim it has seen 100 stops.
        self.train_state[0].update({"stops_seen_so_far" : [1, 2, 3, 4]})

        loader = self._make_component_loader()
        loader._load_world_clock()

        # 2. Execution & Assertion
        # Fails inside Train.__init__ validation logic
        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_trains_raises_error_missing_location(self):
        """
        Verifies that if a train's state has both station_id=None AND
        segment_id=None, the loader raises an exception because the train
        has nowhere to be placed.
        """
        # 1. Setup: Train 1 is nowhere.
        self.train_state[0].update({"station_id": None, "segment_id": None})

        loader = self._make_component_loader()
        loader._load_world_clock()

        # 2. Execution & Assertion
        # Fails inside _assign_train_to_location
        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_stations_raise_error_missing_runtime_state(self):
        self.station_state[1].update({"station_id": 5})
        loader = self._make_component_loader()
        loader._load_world_clock()
        with self.assertRaises(StateLoadingError):
            loader._load_stations()

    def test_load_stations_missing_incoming_rail_segments(self):
        self.segment_config.pop(1)
        loader = self._make_component_loader()
        loader._load_world_clock()
        with self.assertRaises(StateLoadingError):
            loader._load_stations()

    def test_load_stations_missing_outgoing_rail_segments(self):
        self.segment_config.pop(0)
        loader = self._make_component_loader()
        loader._load_world_clock()
        with self.assertRaises(StateLoadingError):
            loader._load_stations()

    def test_load_stations_preserves_multiple_platforms(self):
        """
        Regression Test: Ensures that if a station serves multiple routes (platforms),
        the loader doesn't aggregate them into a single row and lose data.
        """

        # They are the same, since this could happen in overlapping segments
        self.route_config.extend(
            [
                {"route_id": 102, "station_id": 1, "stop_sequence": 1},
                {"route_id": 102, "station_id": 2, "stop_sequence": 2},
            ]
        )

        self.station_state[1].update(
            {"platform_state": PlatformState.TrainArriving.value}
        )

        self.station_state.extend(
            [
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 1,
                    "route_id": 102,
                    "platform_state": PlatformState.Empty.value,
                },
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 2,
                    "route_id": 102,
                    "platform_state": PlatformState.TrainArriving.value,
                },
            ]
        )

        self.train_config[1].update({"route_id": 102, "ordering": 1})
        self.train_state[0].update({"station_id": 2, "stops_seen_so_far": [1]})

        loader = self._make_component_loader()
        loader.load_system_components()

        stations_lookup = loader.get_stations()
        mw_station = stations_lookup[1]
        ep_station = stations_lookup[2]

        self.assertEqual(len(mw_station.platforms), 2, "Should have loaded 2 platforms")
        self.assertEqual(len(ep_station.platforms), 2, "Should have loaded 2 platforms")

        p1 = next(p for p in mw_station.platforms if p.route_id == 101)
        p2 = next(p for p in mw_station.platforms if p.route_id == 102)

        self.assertEqual(p1.platform_state, PlatformState.Empty)
        self.assertEqual(p2.platform_state, PlatformState.Empty)

        p1 = next(p for p in ep_station.platforms if p.route_id == 101)
        p2 = next(p for p in ep_station.platforms if p.route_id == 102)

        self.assertEqual(p1.platform_state, PlatformState.TrainArriving)
        self.assertEqual(p2.platform_state, PlatformState.TrainArriving)

    def test_load_rail_segments_and_assign_trains(self):
        """
        Verifies segments are loaded and trains positioned inside them correctly.
        """
        self.train_config.pop(1)

        self.train_state.pop(1)
        self.train_state[0].update(
            {
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [],
            }
        )
        self.segment_state[0].update({"trains_present": [{"id": 1, "position_km": 5.5}]})
        for state in self.station_state:
            state.update({"platform_state": PlatformState.Empty.value})

        loader = self._make_component_loader()
        loader.load_system_components()

        segments = loader.get_rail_segments()
        segment = segments[0]

        self.assertEqual(segment.id, 99)
        self.assertTrue(segment.has_trains())

        self.assertIn(99, loader.trains_in_segments)
        loaded_train = loader.trains_in_segments[99][0]
        self.assertEqual(loaded_train.get_id(), 1)
        train_in_segment = [train_in_location for train_in_location in list(segment.trains_in_segment) if train_in_location.train.get_id() == 1][0]
        train_position_in_segment = train_in_segment.get_position()
        self.assertEqual(loaded_train.get_id(), 1)
        self.assertEqual(train_position_in_segment, 5.5)
        self.assertIn(
            loaded_train, {train.train for train in list(segment.trains_in_segment)}
        )

    def test_integrity_check_ghost_train_in_undefined_segment(self):
        """
        Verifies that the integrity check raises a ConfigurationError if a train
        is placed in a Rail Segment (e.g., 999) that is not defined in the
        rail_segments configuration.
        """
        # 1. Setup: Hijack Train 1 and put it in the void (Segment 999)
        self.train_state[0].update(
            {
                "station_id": None,
                "segment_id": 999,  # This segment does NOT exist in defaults
                "position_km": 0.5,
                "stops_seen_so_far": [],
            }
        )

        # Ensure our rail segment config is clean (does not contain 999)
        # (The default setUp only creates segment 99)

        # 2. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()

        # Verify the error message specifically mentions the bad segment
        self.assertIn("undefined segment 999", str(cm.exception))

    def test_integrity_check_train_at_undefined_station(self):
        """
        Verifies that the integrity check raises a ConfigurationError if a train
        is placed at a Station ID (e.g., 999) that is not defined in the
        stations configuration.
        """
        # 1. Setup: Place Train 1 at non-existent Station 999
        self.train_state[0].update(
            {
                "station_id": 999,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [],
            }
        )

        # 2. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()

        self.assertIn("undefined Station 999", str(cm.exception))

    def test_integrity_check_detects_asymmetric_circular_loop(self):
        """
        Verifies that the integrity check raises a ConfigurationError even if
        every station has valid incoming and outgoing segments (e.g., A->B->C->A),
        but lacks the required return segments (B->A, C->B, A->C).
        """
        # 1. Setup: Define Stations 1, 2, 3
        self.station_config = [
            {"station_id": 1, "station_name": "A"},
            {"station_id": 2, "station_name": "B"},
            {"station_id": 3, "station_name": "C"},
        ]

        # 2. Setup: Define a One-Way Loop (A -> B -> C -> A)
        # Station 1 has outgoing (to 2) and incoming (from 3) -> Passes basic checks!
        self.segment_config = [
            {
                "segment_id": 10,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10, "speed": 1.0,
            },
            {
                "segment_id": 11,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10, "speed": 1.0,
            },
            {
                "segment_id": 12,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 10, "speed": 1.0,
            },
        ]

        # 3. Setup: Safe Train State (Parked at Station 1)
        # We need a train to avoid "No trains found" errors, but it must be valid
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 100}
        ]
        self.train_state = [
            {
                "clock_tick": self.clock_tick,
                "train_id": 1,
                "station_id": 1,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [],
            }
        ]

        # We need a route to satisfy the train, even if it's dummy
        self.route_config = [
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 3, "stop_sequence": 3},
            {"route_id": 101, "station_id": 1, "stop_sequence": 4},
        ]

        # Need station state for the 3 stations
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
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 101,
                "platform_state": PlatformState.Empty.value,
            },
        ]
        loader = self._make_component_loader()
        # 4. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:

            loader.load_system_components()

        # The error should specifically catch that 1->2 exists but 2->1 does not
        self.assertIn("no return segment", str(cm.exception))

    def test_integrity_check_magic_carpet_segment_not_on_route(self):
        """
        Verifies that the integrity check raises a ConfigurationError if a train
        is on a valid Rail Segment, but that segment represents a path
        NOT present in the train's assigned Route.
        """

        self.station_config.append({"station_id": 3, "station_name": "Three Station"})

        self.route_config.extend(
            [
                {"route_id": 205, "station_id": 3, "stop_sequence": 1},
                {"route_id": 205, "station_id": 2, "stop_sequence": 2},
            ]
        )

        self.station_state.append(
            {
                "clock_tick": self.clock_tick,
                "station_id": 3,
                "route_id": 205,
                "platform_state": PlatformState.Empty.value,
            }
        )
        # 1. Setup: Create a "Magic" Segment (1->3) that exists physically...
        self.segment_config.append(
            {
                "segment_id": 500,
                "from_station_id": 1,
                "to_station_id": 3,  # Skipping station 2!
                "distance_km": 50.0,
                "speed": 1.0,
            }
        )
        # (Add return segment to pass symmetry check)
        self.segment_config.append(
            {
                "segment_id": 501,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 50.0,
                "speed": 1.0,
            }
        )

        self.segment_state.extend([
            {
                "clock_tick": self.clock_tick,
                "segment_id": 500,
                "trains_present": [{"id": 1, "position_km": 10.0}] # Matches Train 1's position
            },
            {
                "clock_tick": self.clock_tick,
                "segment_id": 501,
                "trains_present": []
            }
        ])

        # 2. Setup: Put Train 1 (Route 101: 1->2->1) onto this Magic Segment (1->3)
        self.train_state[0].update(
            {
                "station_id": None,
                "segment_id": 500,  # Valid segment ID...
                "position_km": 10.0,
            }
        )

        # 3. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()

        # The error should complain that transition 1->3 is not in Route 101
        self.assertIn("transition is not part of its Route", str(cm.exception))

    def test_integrity_check_station_missing_platform_for_route(self):
        """
        Verifies that if a Station is listed in a Route's path, but that Station
        does not have a Platform configured for that Route ID, a ConfigurationError is raised.
        """

        self.route_config.extend(
            [
                {"route_id": 102, "station_id": 1, "stop_sequence": 1},
                {"route_id": 102, "station_id": 2, "stop_sequence": 2},
            ]
        )

        self.train_config[1].update({"route_id": 102, "ordering": 1})
        self.train_state[0].update({"station_id": 2, "stops_seen_so_far": [1]})

        loader = self._make_component_loader()

        # 3. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:

            loader.load_system_components()

        self.assertIn("has no platform configured", str(cm.exception))

    def test_integrity_check_platform_for_nonexistent_route(self):
        """
        Verifies that if a Station has a Platform configured for a Route ID
        that does not exist in the route definitions, a ConfigurationError is raised.
        """
        # 1. Setup: Route 101 exists
        self.station_state.append(
            {
                "clock_tick": self.clock_tick,
                "station_id": 2,
                "route_id": 404,
                "platform_state": PlatformState.Empty.value,
            }
        )

        loader = self._make_component_loader()

        # 3. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:
            loader.load_system_components()

        self.assertIn("not defined in train routes", str(cm.exception))

    def test_integrity_check_route_connectivity_missing_segment(self):
        """
        Verifies that if a Route implies travel between two stations (e.g., 1->3)
        but no direct rail segment exists between them, a ConfigurationError is raised.
        """
        # 1. Setup: Route 101 wants to go 1 -> 3 directly
        self.route_config = [
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 3, "stop_sequence": 2},
            {"route_id": 102, "station_id": 1, "stop_sequence": 1},
            {"route_id": 102, "station_id": 2, "stop_sequence": 2},
            {"route_id": 102, "station_id": 3, "stop_sequence": 3},
        ]

        # 2. Setup: Physical track only connects 1->2 and 2->3 (No 1->3)
        self.segment_config = [
            {
                "segment_id": 1,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10, "speed": 1.0,
            },
            {
                "segment_id": 2,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10, "speed": 1.0,
            },
            # Return paths
            {
                "segment_id": 3,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 10, "speed": 1.0,
            },
            {
                "segment_id": 4,
                "from_station_id": 3,
                "to_station_id": 2,
                "distance_km": 10, "speed": 1.0,
            },
        ]

        # (Minimal valid config)
        self.station_config = [
            {"station_id": 1, "station_name": "A"},
            {"station_id": 2, "station_name": "B"},
            {"station_id": 3, "station_name": "C"},
        ]
        self.station_state.extend(
            [
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 1,
                    "route_id": 102,
                    "platform_state": PlatformState.Empty.value,
                },
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 2,
                    "route_id": 102,
                    "platform_state": PlatformState.Empty.value,
                },
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 3,
                    "route_id": 102,
                    "platform_state": PlatformState.Empty.value,
                },
                {
                    "clock_tick": self.clock_tick,
                    "station_id": 3,
                    "route_id": 101,
                    "platform_state": PlatformState.Empty.value,
                },
            ]
        )
        # Train 1 on Route 101
        self.train_config.pop(1)
        self.train_state.pop(1)

        # 3. Execution & Assertion
        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()

        self.assertIn("no connecting rail segment exists", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
