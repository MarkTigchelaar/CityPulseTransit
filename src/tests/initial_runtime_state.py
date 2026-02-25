from initial_loader_state import InitialLoaderState
from simulation.component_loader import ComponentLoader
from transit_system import TransitSystem
from memory_producer import MemoryProducer

class InitialRuntimeState(InitialLoaderState):
    def setUp(self):
        super().setUp()
        self.component_loader: ComponentLoader = None
        self.transit_system: TransitSystem = None
        self.train_config = []
        self.train_state = []
        self.passenger_itinerary = []
        self.passenger_routes = []
        self.passenger_state = []
        self.producer = MemoryProducer()
        self.producer.clear()

    def load_system(self):
        self.component_loader = self._make_component_loader()
        self.transit_system = TransitSystem(self.component_loader)

    def get_current_clock_tick(self) -> int:
        if self.component_loader is None:
            raise Exception("Component loader not initialized. Call load_system first.")
        return self.component_loader.get_world_clock().get_current_clock_tick()
    
    def run_once(self):
        if self.transit_system is None:
            raise Exception("Transit system not initialized. Call load_system first.")
        self.transit_system.run_once()

    def _run_until_passenger_at_station(self, passenger_id, station_id, max_ticks):
        for _ in range(max_ticks):
            self.run_once()
            events = self.producer.get_events("passenger_travelling_state")
            for e in reversed(events):
                if e["passenger_id"] == passenger_id and e["station_id"] == station_id:
                    return
        raise Exception(f"Passenger {passenger_id} did not arrive at Station {station_id} within {max_ticks} ticks")
