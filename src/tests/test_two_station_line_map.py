import unittest
from two_station_line_map import TwoStationLineMap


class TestTwoStationLineMap(TwoStationLineMap):
    def test_load_and_run_ticks(self):
        self.load_system()
        self.run_once()
        current_tick = self.get_current_clock_tick()
        self.assertEqual(current_tick, 1, "Clock should have advanced 1 tick")
        self.assertEqual(len(self.component_loader.get_stations()), 2)
        self.assertEqual(len(self.component_loader.get_rail_segments()), 2)


if __name__ == "__main__":
    unittest.main()
