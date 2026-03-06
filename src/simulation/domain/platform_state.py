from enum import Enum


class PlatformState(Enum):
    Empty = "Empty"
    TrainArriving = "Arrival"
    MovingPassengers = "MovingPassengers"
    TrainDeparting = "Departure"

    def __eq__(self, other):
        if isinstance(other, PlatformState):
            return self.value == other.value
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    @staticmethod
    def from_code(platform_state_code) -> "PlatformState":
        for member in PlatformState:
            if member.value == platform_state_code:
                return member
        raise ValueError(f"No platform state with code {platform_state_code}")

    @staticmethod
    def next_state(platform_state: "PlatformState") -> "PlatformState":
        state_sequence = {
            PlatformState.Empty: PlatformState.TrainArriving,
            PlatformState.TrainArriving: PlatformState.MovingPassengers,
            PlatformState.MovingPassengers: PlatformState.TrainDeparting,
            PlatformState.TrainDeparting: PlatformState.Empty,
        }

        if platform_state in state_sequence:
            return state_sequence[platform_state]

        raise ValueError(
            f"Cannot determine 'next platform state' for a platform in state: {platform_state.name}"
        )
