from enum import Enum


class TravelDays(Enum):
    Monday = 'M'
    Tuesday = 'T'
    Wednesday = 'W'
    Thursday = 'R'
    Friday = 'F'
    Saturday = 'S'
    Sunday = 'U'

    MonWedFri = 'MWF'
    TueThur = 'TU'
    WorkWeek = 'MTWRF'
    Weekend = 'SU'
    Daily = 'MTWRFSU'

    def __eq__(self, other):
        if isinstance(other, TravelDays):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
        return hash(self.value)

    @staticmethod
    def from_code(travel_days_code):
        for member in TravelDays:
            if member.value == travel_days_code:
                return member
        raise ValueError(f"No travel code with value {travel_days_code}")

    @staticmethod
    def next_day(self) -> str:
        day_sequence = {
            TravelDays.Monday: TravelDays.Tuesday,
            TravelDays.Tuesday: TravelDays.Wednesday,
            TravelDays.Wednesday: TravelDays.Thursday,
            TravelDays.Thursday: TravelDays.Friday,
            TravelDays.Friday: TravelDays.Saturday,
            TravelDays.Saturday: TravelDays.Sunday,
            TravelDays.Sunday: TravelDays.Monday
        }

        if self in day_sequence:
            return day_sequence[self]
        
        raise ValueError(f"Cannot determine 'next day' for a schedule group: {self.name}")
