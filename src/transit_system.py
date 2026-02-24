from simulation.component_loader import ComponentLoader
from simulation.table_data_reader import TableDataReader
from simulation.producer import LiveProducer
import time

class TransitSystem:
    def __init__(self, component_loader: ComponentLoader):
        component_loader.load_system_components()

        self.stations = component_loader.get_stations()
        self.trains = component_loader.get_trains()
        self.rail_segments = component_loader.get_rail_segments()
        self.passengers = component_loader.get_passengers()
        self.world_clock = component_loader.get_world_clock()
        print("Transit system is ready.")


    def down(self):
        print("Transit system has been shut down.")

    def run(self):
        print("Transit system is running.")
        for i in range(200):
            print(f"--- ⏱️ Tick {i+1} ---")
            self.run_once()
            time.sleep(1)
        print("🛑 Debug Run Complete.")
            
    def run_once(self):
        self.world_clock.tick()
        
        self._process_passengers()
        self._process_stations()
        self._process_rail_segments()

    def _process_passengers(self):
        for passenger in self.passengers:
            if passenger.is_in_system():
                continue
            if passenger.ready_to_start_travelling():
                station_id = passenger.start_travelling()
                self.stations[station_id].passenger_enter_station(passenger)      

    def _process_stations(self):
        for station_id in self.stations:
            self.stations[station_id].process()

    def _process_rail_segments(self):
        for segment in self.rail_segments:
            segment.process()

if __name__ == "__main__":
    time.sleep(5)
    data_reader = TableDataReader()
    producer = LiveProducer()
    component_loader = ComponentLoader(data_reader, producer)
    transit_system = TransitSystem(component_loader)
    transit_system.run()

