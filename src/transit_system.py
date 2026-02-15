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
        self.user_variables = component_loader.get_user_adjustable_variables()
        print("Transit system is ready.")


    def down(self):
        print("Transit system has been shut down.")

    def run(self):
        print("Transit system is running.")
        for _ in range(20):
            self.run_once()
            time.sleep(1)
            
    def run_once(self):
        self.world_clock.tick()
        
        self._process_passengers()
        self._process_stations()
        self._process_rail_segments()
        self.user_variables.send_update(self.world_clock.get_current_clock_tick())

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
    data_reader = TableDataReader()
    producer = LiveProducer()
    component_loader = ComponentLoader(data_reader, producer)
    transit_system = TransitSystem(component_loader)
    transit_system.run()

