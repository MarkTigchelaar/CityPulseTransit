from enum import Enum

TRAIN_LIMIT_PER_SEGMENT = 75


class PlatformState(Enum):
    Empty = "Empty"
    TrainArriving = "Arrival"
    MovingPassengers = "MovingPassengers"
    TrainDeparting = "Departure"

    def __eq__(self, other):
        if isinstance(other, PlatformState):
            return self.value == other.value
        return self.value == other

    @staticmethod
    def from_code(platform_state_code) -> 'PlatformState':
        for member in PlatformState:
            if member.value == platform_state_code:
                return member
        raise ValueError(f"No platform state with code {platform_state_code}")
