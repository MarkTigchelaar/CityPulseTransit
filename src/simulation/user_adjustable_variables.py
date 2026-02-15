from simulation.system_event_bus import SystemEventBus

class UserAdjustableVariables:
    def __init__(self, clock_rate: int, train_speed: float, system_event_bus: SystemEventBus):
        self.clock_rate = clock_rate
        self.train_speed = train_speed
        self.system_event_bus = system_event_bus

    def get_clock_rate(self) -> int:
        return self.clock_rate
    
    def get_train_speed(self) -> float:
        return self.train_speed
    
    def send_update(self, clock_tick) -> None:
        self.system_event_bus.log_user_adjustable_variables(
            {
                "clock_tick": clock_tick,
                "clock_rate": self.clock_rate,
                "train_speed": self.train_speed
            }
        )
