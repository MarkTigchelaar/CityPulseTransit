import unittest
from src.simulation.domain.platform_state import PlatformState
from src.simulation.domain.travel_days import TravelDays
from src.simulation.bootstrap.component_loader import StateLoadingError, ConfigurationError
from initial_states.initial_loader_state import InitialLoaderState


class TestComponentLoader(InitialLoaderState):

    def test_load_world_clock(self):
        loader = self._make_component_loader()
        loader._load_world_clock()
        clock = loader.get_world_clock()
        self.assertEqual(clock.clock_tick, self.clock_tick)
        self.assertEqual(clock.day_of_week, TravelDays.Monday)

    def test_load_passenger_starts_in_train(self):
        self.passenger_state[0].update(
            {
                "train_id": 1,
                "station_id": None,
                "stops_seen_so_far": [1],
            }
        )

        loader = self._make_component_loader()
        loader.load_system_components()

        trains = loader.get_trains()
        target_train = next(t for t in trains if t.get_id() == 1)
        other_trains = [t for t in trains if t.get_id() != 1]

        self.assertIn(
            1, target_train.passengers, "Passenger 1 should be inside Train 1"
        )
        for train in other_trains:
            self.assertNotIn(
                1, train.passengers, "Passenger 1 should be inside Train 1"
            )

        passenger = target_train.passengers[1]
        self.assertTrue(
            passenger.is_travelling, "Passenger should be marked as travelling"
        )
        self.assertEqual(passenger.visited_station_ids, [1])

        stations = loader.get_stations()
        for station_id in stations:
            target_station = stations[station_id]

            passenger_ids_in_station = [p.get_id() for p in target_station.passengers]
            self.assertNotIn(
                1,
                passenger_ids_in_station,
                "Passenger 1 should be inside train, not in station",
            )

    def test_load_passenger_starts_in_station(self):
        self.passenger_state[0].update(
            {
                "train_id": None,
                "station_id": 1,
                "stops_seen_so_far": [],
            }
        )

        loader = self._make_component_loader()
        loader.load_system_components()

        stations = loader.get_stations()
        target_station = stations[1]

        passenger_ids_in_station = [p.get_id() for p in target_station.passengers]
        self.assertIn(
            1, passenger_ids_in_station, "Passenger 1 should be inside Station 1"
        )

        for train in loader.get_trains():
            self.assertNotIn(1, train.passengers)

    def test_load_passengers_raises_error_missing_route_definition(self):
        self.passenger_itinerary.append(
            {
                "id": 1,
                "passenger_route_id": 999,
                "start_arrival_hour": 8,
                "arrival_minute": 0,
                "travel_code": "12345",
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
        with self.assertRaises(ConfigurationError):
            loader._load_passengers()

    def test_load_passengers_raises_error_missing_runtime_state(self):
        self.passenger_state[0].update({"passenger_id": 2})

        loader = self._make_component_loader()
        loader._load_world_clock()

        with self.assertRaises(StateLoadingError):
            loader._load_passengers()

    def test_load_passengers_raises_error_invalid_travel_days_code(self):
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

        with self.assertRaises(ConfigurationError):
            loader._load_passengers()

    def test_load_trains_correctly_assigns_attributes(self):
        self.train_state[0].update({"stops_seen_so_far": [1, 2]})
        loader = self._make_component_loader()
        loader.load_system_components()

        trains = loader.get_trains()
        t1 = next(t for t in trains if t.get_id() == 1)
        t2 = next(t for t in trains if t.get_id() == 2)
        # very important this loads correctly.
        # routes are compared to this, and when equal that is
        # the completion of the route. Passegners get off trains and leave
        # trains repeat from beginning of route.
        self.assertEqual(
            t1.station_ids_visited, [1, 2], "Train 1 should have 2 stops seen"
        )
        self.assertEqual(
            t2.station_ids_visited, [1], "Train 2 should have 1 stops seen"
        )

    def test_load_trains_raises_error_missing_route_definition(self):
        self.train_config.append(
            {
                "train_id": 99,
                "route_id": 999,
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

        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_trains_raises_error_missing_runtime_state(self):
        self.train_config.append(
            {"train_id": 99, "route_id": 101, "ordering": 1, "capacity": 100}
        )

        # train 99 not in train state, will fail
        loader = self._make_component_loader()
        loader._load_world_clock()

        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_trains_raises_error_invalid_stops_seen_count(self):
        self.train_state[0].update({"stops_seen_so_far": [1, 2, 3, 4]})

        loader = self._make_component_loader()
        loader._load_world_clock()
        with self.assertRaises(StateLoadingError):
            loader._load_trains()

    def test_load_trains_raises_error_missing_location(self):
        # Train 1 is nowhere.
        self.train_state[0].update({"station_id": None, "segment_id": None})

        loader = self._make_component_loader()
        loader._load_world_clock()

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
        self.train_config.pop(1)
        self.train_state.pop(1)
        self.train_state[0].update(
            {
                "station_id": None,
                "segment_id": 99,
                "stops_seen_so_far": [],
            }
        )
        self.segment_state[0].update(
            {"trains_present": [{"id": 1, "position_km": 5.5}]}
        )
        for state in self.station_state:
            state.update({"platform_state": PlatformState.Empty.value})

        loader = self._make_component_loader()
        loader.load_system_components()

        segments = loader.get_rail_segments()
        segment = segments[0]

        self.assertEqual(segment.get_id(), 99)
        self.assertTrue(segment.has_trains())

        self.assertIn(99, loader.trains_in_segments)
        loaded_train = loader.trains_in_segments[99][0]
        self.assertEqual(loaded_train.get_id(), 1)
        train_in_segment = [
            train_in_location
            for train_in_location in list(segment.trains_in_segment)
            if train_in_location.train.get_id() == 1
        ][0]
        train_position_in_segment = train_in_segment.get_position()
        self.assertEqual(loaded_train.get_id(), 1)
        self.assertEqual(train_position_in_segment, 5.5)
        self.assertIn(
            loaded_train, {train.train for train in list(segment.trains_in_segment)}
        )

    def test_integrity_check_ghost_train_in_undefined_segment(self):
        self.train_state[0].update(
            {
                "station_id": None,
                "segment_id": 999,  # This segment does NOT exist in default config
                "position_km": 0.5,
                "stops_seen_so_far": [],
            }
        )

        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()
        self.assertIn("undefined segment 999", str(cm.exception))

    def test_integrity_check_train_at_undefined_station(self):
        self.train_state[0].update(
            {
                "station_id": 999,
                "segment_id": None,
                "position_km": 0,
                "stops_seen_so_far": [],
            }
        )
        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()
        self.assertIn("undefined Station 999", str(cm.exception))

    def test_integrity_check_detects_asymmetric_circular_loop(self):
        self.station_config = [
            {"station_id": 1, "station_name": "A"},
            {"station_id": 2, "station_name": "B"},
            {"station_id": 3, "station_name": "C"},
        ]

        # Define a One-Way Loop (A -> B -> C -> A)
        self.segment_config = [
            {
                "segment_id": 10,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 11,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 12,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 10,
                "speed": 1.0,
            },
        ]

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

        self.route_config = [
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 2, "stop_sequence": 2},
            {"route_id": 101, "station_id": 3, "stop_sequence": 3},
            {"route_id": 101, "station_id": 1, "stop_sequence": 4},
        ]

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

        with self.assertRaises(ConfigurationError) as cm:
            loader.load_system_components()
        self.assertIn("no return segment", str(cm.exception))

    def test_integrity_check_magic_carpet_segment_not_on_route(self):
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
        # "Magic" Segment (1->3)
        self.segment_config.append(
            {
                "segment_id": 500,
                "from_station_id": 1,
                "to_station_id": 3,
                "distance_km": 50.0,
                "speed": 1.0,
            }
        )
        self.segment_config.append(
            {
                "segment_id": 501,
                "from_station_id": 3,
                "to_station_id": 1,
                "distance_km": 50.0,
                "speed": 1.0,
            }
        )

        self.segment_state.extend(
            [
                {
                    "clock_tick": self.clock_tick,
                    "segment_id": 500,
                    "trains_present": [
                        {"id": 1, "position_km": 10.0}
                    ],  # Matches Train 1's position
                },
                {
                    "clock_tick": self.clock_tick,
                    "segment_id": 501,
                    "trains_present": [],
                },
            ]
        )

        # Train 1 onto Magic Segment (1->3)
        self.train_state[0].update(
            {
                "station_id": None,
                "segment_id": 500,
                "position_km": 10.0,
            }
        )

        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()
        self.assertIn("transition is not part of its Route", str(cm.exception))

    def test_integrity_check_station_missing_platform_for_route(self):
        self.route_config.extend(
            [
                {"route_id": 102, "station_id": 1, "stop_sequence": 1},
                {"route_id": 102, "station_id": 2, "stop_sequence": 2},
            ]
        )

        self.train_config[1].update({"route_id": 102, "ordering": 1})
        self.train_state[0].update({"station_id": 2, "stops_seen_so_far": [1]})
        loader = self._make_component_loader()
        with self.assertRaises(ConfigurationError) as cm:
            loader.load_system_components()
        self.assertIn("has no platform configured", str(cm.exception))

    def test_integrity_check_platform_for_nonexistent_route(self):
        self.station_state.append(
            {
                "clock_tick": self.clock_tick,
                "station_id": 2,
                "route_id": 404,
                "platform_state": PlatformState.Empty.value,
            }
        )
        loader = self._make_component_loader()
        with self.assertRaises(ConfigurationError) as cm:
            loader.load_system_components()
        self.assertIn("not defined in train routes", str(cm.exception))

    def test_integrity_check_route_connectivity_missing_segment(self):
        self.route_config = [
            {"route_id": 101, "station_id": 1, "stop_sequence": 1},
            {"route_id": 101, "station_id": 3, "stop_sequence": 2},
            {"route_id": 102, "station_id": 1, "stop_sequence": 1},
            {"route_id": 102, "station_id": 2, "stop_sequence": 2},
            {"route_id": 102, "station_id": 3, "stop_sequence": 3},
        ]

        # track only connects 1->2 and 2->3 (No 1->3)
        self.segment_config = [
            {
                "segment_id": 1,
                "from_station_id": 1,
                "to_station_id": 2,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 2,
                "from_station_id": 2,
                "to_station_id": 3,
                "distance_km": 10,
                "speed": 1.0,
            },
            # Return paths
            {
                "segment_id": 3,
                "from_station_id": 2,
                "to_station_id": 1,
                "distance_km": 10,
                "speed": 1.0,
            },
            {
                "segment_id": 4,
                "from_station_id": 3,
                "to_station_id": 2,
                "distance_km": 10,
                "speed": 1.0,
            },
        ]

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

        with self.assertRaises(ConfigurationError) as cm:
            loader = self._make_component_loader()
            loader.load_system_components()

        self.assertIn("no connecting rail segment exists", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
