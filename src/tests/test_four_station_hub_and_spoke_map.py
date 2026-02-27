from system_maps.four_station_hub_and_spoke_map import FourStationHubAndSpokeMap
import unittest

class TestFourStationHubAndSpokeMap(FourStationHubAndSpokeMap):
    def test_load_and_run_ticks(self):
        self.load_system()
        self.run_once()
        hub = self.component_loader.get_stations()[1]
        self.assertEqual(len(hub.platforms), 3, "Hub should have 3 platforms (one per route)")
        
        self.assertEqual(len(self.component_loader.get_stations()), 4)
        self.assertEqual(len(self.component_loader.get_rail_segments()), 6)

if __name__ == "__main__":
    unittest.main()