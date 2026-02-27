from system_maps.three_station_line_map import ThreeStationLineMap
import unittest


class TestThreeStationLineMap(ThreeStationLineMap):
    def test_load_and_run_ticks(self):
        self.load_system()
        self.run_once()
        current_tick = self.get_current_clock_tick()
        self.assertEqual(current_tick, 1, "Clock should have advanced 1 tick")
        self.assertEqual(
            len(self.component_loader.get_stations()), 3, "Should still have 3 stations"
        )
        self.assertEqual(
            len(self.component_loader.get_rail_segments()),
            4,
            "Should still have 4 rail segments",
        )


if __name__ == "__main__":
    unittest.main()
