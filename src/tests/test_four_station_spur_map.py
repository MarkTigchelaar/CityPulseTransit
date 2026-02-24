from four_station_spur_map import FourStationSpurMap
import unittest

class TestFourStationSpurMap(FourStationSpurMap):
    def test_load_and_run_ticks(self):
        self.load_system()
        self.run_once()
        
        # Verify Junction Station 3 has 3 outgoing connections (to 1, 2, and 4)
        #junction = self.component_loader.get_stations()[3]
        # Note: Depending on your implementation, this might check rail segments
        # or the logical route connections.
        
        self.assertEqual(len(self.component_loader.get_stations()), 4)
        self.assertEqual(len(self.component_loader.get_rail_segments()), 8)

if __name__ == "__main__":
    unittest.main()
