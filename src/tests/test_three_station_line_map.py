from three_station_line_map import ThreeStationLineMap
import unittest

class TestThreeStationLineMap(ThreeStationLineMap):
    """
    Proves that the ThreeStationLineMap base class can load and run.
    """

    def test_load_and_run_ticks(self):
        """
        Verifies that the topology loads correctly and runs for 1 clock tick
        without raising any exceptions.
        """

        self.load_system()
        self.run_once()
            
        current_tick = self.get_current_clock_tick()

        self.assertEqual(current_tick, 1, "Clock should have advanced 1 tick")
        self.assertEqual(len(self.component_loader.get_stations()), 3, "Should still have 3 stations")
        self.assertEqual(len(self.component_loader.get_rail_segments()), 4, "Should still have 4 rail segments")

if __name__ == "__main__":
    unittest.main()