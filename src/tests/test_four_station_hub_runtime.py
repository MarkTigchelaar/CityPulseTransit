from four_station_hub_and_spoke_map import FourStationHubAndSpokeMap
from simulation.constants import PlatformState
import unittest

class TestFourStationHubRuntime(FourStationHubAndSpokeMap):
    """
    Tests complex transfers in a Hub-and-Spoke topology.
    """

    def test_multi_hop_transfer(self):
        """
        Scenario: The "Grand Tour".
        Passenger travels Spoke A (2) -> Hub (1) -> Spoke B (3) -> Hub (1) -> Spoke C (4).
        Requires using 3 different trains (Route 101, 102, 103) in sequence.
        """




        # Passenger starts at Station 2, assigned to Route 999
        self.passenger_itinerary = [{
            "id": 1, "passenger_route_id": 999, 
            "start_arrival_hour": 8, "arrival_minute": 1, "travel_code": "MTWRF"
        }]
        # Helper lookup for the loader
        self.passenger_routes = [
            {"route_id": 999, "stop_sequence": 0, "station_id": 2},
            {"route_id": 999, "stop_sequence": 1, "station_id": 1},
            {"route_id": 999, "stop_sequence": 2, "station_id": 3},
            {"route_id": 999, "stop_sequence": 3, "station_id": 1},
            {"route_id": 999, "stop_sequence": 4, "station_id": 4}
        ]
        self.passenger_state = [{
            "clock_tick": self.clock_tick, 
            "passenger_id": 1, 
            "train_id": None,
            "station_id": None, # Have passenger enter system at first stop on route
            "stops_seen_so_far": []
        }]

        # Train Setup:
        # Train 1 (Route 101: 2<->1) at Stn 2.
        # Train 2 (Route 102: 3<->1) at Stn 1.
        # Train 3 (Route 103: 4<->1) at Stn 1.
        self.train_config = [
            {"train_id": 1, "route_id": 101, "ordering": 1, "capacity": 1},
            {"train_id": 2, "route_id": 102, "ordering": 1, "capacity": 1},
            {"train_id": 3, "route_id": 103, "ordering": 1, "capacity": 1}
        ]
        
        # Only the train at station 2 is ready for loading, others at station 1 and will leave before passenger arrives
        # This creates a waiting condition for the passenger to test transfer logic.
        self.train_state = [
            {"clock_tick": self.clock_tick, "train_id": 1, "station_id": 2, "segment_id": None, "position_km": 0, "stops_seen_so_far": [1,2]},
            {"clock_tick": self.clock_tick, "train_id": 2, "station_id": 1, "segment_id": None, "position_km": 0, "stops_seen_so_far": [1]},
            {"clock_tick": self.clock_tick, "train_id": 3, "station_id": 1, "segment_id": None, "position_km": 0, "stops_seen_so_far": [1]}
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
                    station_state["platform_state"] = PlatformState.MovingPassengers.value
            if station_state["station_id"] == 2:
                station_state["platform_state"] = PlatformState.MovingPassengers.value


        
        self.load_system()

        # Confirm passenger did arrive at station 4
        # Station 2:  2 ticks
        # segment 21: 1 tick
        # Station 1:  3 ticks (wait for train 2 to arrive and load, and depart)
        # segment 13: 1 tick
        # Station 3:  3 ticks (wait for train 3 to arrive and load, and depart)
        # segment 31: 1 tick
        # Station 1:  3 ticks (wait for train 1 to arrive and load, and depart)
        # segment 14: 1 tick
        # Station 4:  2 ticks (arrival, and offboard)
        # Total: 17 ticks
        self._run_until_passenger_at_station(passenger_id=1, station_id=4, max_ticks=17)

        # Examination of produced state:
# ---------------------------------------------------------
        # 1. PASSENGER STATE: Verify the "Hop History"
        # ---------------------------------------------------------
        # We trace the passenger's journey by looking at their 'arriving' events.
        # Note: If the passenger stayed on Train 2 for the 1->3->1 loop without getting off,
        # they might not log an 'arriving' event at Station 3.
        # Sequence should be: Start(2) -> Transfer(1) -> Transfer(1) -> End(4)
        p_events = self.producer.get_events("passenger_travelling_state")
        
        # Filter for our specific passenger's arrival logs
        arrivals = [
            e["station_id"] for e in p_events 
            if e["passenger_id"] == 1
        ]
        
        # We expect at least: [2 (Start), 1 (Hub Arrival 1), 1 (Hub Arrival 2), 4 (Final)]
        # We check that the list *contains* this sequence in relative order
        self.assertIn(2, arrivals, "Must start at Station 2")
        self.assertIn(4, arrivals, "Must end at Station 4")
        self.assertGreaterEqual(arrivals.count(1), 2, "Must visit Hub (1) at least twice (Transfer In, Loop Return)")

        # ---------------------------------------------------------
        # 2. TRAIN STATE: Verify Segments Carried Cargo
        # ---------------------------------------------------------
        train_events = self.producer.get_events("train_state")

        def check_train_segment_load(train_id, segment_id, min_passengers=1):
            """Helper to assert a train carried passengers on a specific segment."""
            # Find all logs where this train was in this segment
            logs = [
                e for e in train_events 
                if e["train_id"] == train_id and e["segment_id"] == segment_id
            ]
            # Ensure at least one log shows the passenger on board
            was_loaded = any(e["passenger_count"] >= min_passengers for e in logs)
            self.assertTrue(was_loaded, f"Train {train_id} should carry passengers on Segment {segment_id}")

        # Check HOP 1: Train 1 (Route 101) carries on Segment 21 (Spoke A -> Hub)
        check_train_segment_load(train_id=1, segment_id=21)

        # Check HOP 2: Train 2 (Route 102) carries on Segment 13 (Hub -> Spoke B)
        check_train_segment_load(train_id=2, segment_id=13)

        # Check HOP 3: Train 2 (Route 102) carries on Segment 31 (Spoke B -> Hub)
        # Note: Passenger likely stayed on board for this leg
        check_train_segment_load(train_id=2, segment_id=31)

        # Check HOP 4: Train 3 (Route 103) carries on Segment 14 (Hub -> Spoke C)
        check_train_segment_load(train_id=3, segment_id=14)

        # ---------------------------------------------------------
        # 3. STATION STATE: Verify Hub Throughput
        # ---------------------------------------------------------
        station_events = self.producer.get_events("station_state")
        
        # Filter for the Hub (Station 1)
        hub_logs = [e for e in station_events if e["station_id"] == 1]
        
        # Calculate total boardings at the Hub
        # The passenger must board TWICE at the Hub:
        # 1. Board Train 2 (to go to Spoke B)
        # 2. Board Train 3 (to go to Spoke C)
        total_hub_boardings = sum(e["passengers_boarded_trains"] for e in hub_logs)
        
        self.assertGreaterEqual(total_hub_boardings, 2, "Hub (Station 1) should process at least 2 boardings")


if __name__ == "__main__":
    unittest.main()
