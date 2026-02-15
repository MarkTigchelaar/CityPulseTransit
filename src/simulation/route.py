"""
This is the closest thing to a brain that passengers and trains will have in this simulation.
It is responsible for determining the next station a train or passenger should go to,
based on the route configuration and the stops it has seen so far.
"""

class Route:
    def __init__(self, route_id: int, station_ids: list[int], stops: list[int]):
        self.id = route_id
        self.station_ids = station_ids
        self.stops = stops

    def get_id(self) -> int:
        return self.id

    def get_station_ids(self) -> list[int]:
        return self.station_ids

    def route_complete(self, stops_seen_so_far: list[int]) -> bool:
        if len(self.station_ids) != len(stops_seen_so_far):
            return False
        return self.station_ids == stops_seen_so_far

    def get_next_station_id(self, stops_seen_so_far: list[int], station_id: int) -> int:
        # Routing problems are data corruption, halt program
        if len(set(stops_seen_so_far) - set(self.station_ids)) > 0:
            raise Exception(
                f"Stops not found in route stops({self.station_ids}): {stops_seen_so_far}"
            )
        most_recent_stop_id = stops_seen_so_far[-1]
        if most_recent_stop_id != station_id:
            raise Exception(
                f"Current station id {station_id} does not match expected current station id {most_recent_stop_id}"
            )
        if most_recent_stop_id not in self.station_ids:
            raise Exception("Station ID not found on this route.")
        if self.station_ids[len(stops_seen_so_far) - 1] != stops_seen_so_far[-1]:
            raise Exception(f"Station id does not match the one at the matching index")
        next_station_index = len(stops_seen_so_far)
        if next_station_index < len(self.station_ids):
            return self.station_ids[next_station_index]
        else:
            return None
