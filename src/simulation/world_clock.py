from simulation.constants import TravelDays
from simulation.system_event_bus import SystemEventBus


class WorldClock:
    def __init__(
        self,
        clock_tick: int,
        day_of_week: str,
        year: int,
        day_of_year: int,
        hour_of_day: int,
        minute: int,
        system_event_bus: SystemEventBus,
    ):
        self.clock_tick = clock_tick
        self.day_of_week: str = TravelDays.from_code(day_of_week)
        self.day_of_year = day_of_year
        self.year = year
        self.hour_of_day = hour_of_day
        self.minute = minute
        self.system_event_bus = system_event_bus


    def get_current_clock_tick(self) -> int:
        return self.clock_tick

    def get_clock_rate(self) -> int:
        return self.clock_rate_adjuster.get_clock_rate()

    def tick(self):
        self.clock_tick += 1
        self.minute += 1
        if self.minute > 59:
            self.minute = 0
            self.hour_of_day += 1
        if self.hour_of_day > 23:
            self.hour_of_day = 0
            self.minute = 0
            self.day_of_week = TravelDays.next_day(self.day_of_week)
            self.day_of_year += 1
        if self.day_of_year > 365:
            self.year += 1
            self.day_of_year = 1
        self._send_time_update_event()

    def _send_time_update_event(self):
        self.system_event_bus.log_world_clock_state(
            {
                "clock_tick": self.clock_tick,
                "day_of_week": self.day_of_week.value,
                "year": self.year,
                "day_of_year": self.day_of_year,
                "hour_of_day": self.hour_of_day,
                "minute": self.minute,
            },
        )

    def get_day_of_week(self) -> TravelDays:
        return self.day_of_week

    def get_hour(self) -> int:
        return self.hour_of_day

    def get_minute(self) -> int:
        return self.minute
