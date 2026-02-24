from three_station_circle_map import ThreeStationCircleMap
import unittest

class TestThreeStationCircleMap(ThreeStationCircleMap):
    """
    Proves that the ThreeStationCircleMap topology loads and runs.
    """

    def test_load_and_run_ticks(self):
        """
        Verifies that the topology loads correctly and runs for 1 clock tick
        without raising any exceptions.
        Checks for 3 stations and 6 rail segments.
        """

        self.load_system()
        self.run_once()
            
        current_tick = self.get_current_clock_tick()

        self.assertEqual(current_tick, 1, "Clock should have advanced 1 tick")
        self.assertEqual(len(self.component_loader.get_stations()), 3, "Should have 3 stations")
        self.assertEqual(len(self.component_loader.get_rail_segments()), 6, "Should have 6 rail segments (3 pairs * 2)")

if __name__ == "__main__":
    unittest.main()