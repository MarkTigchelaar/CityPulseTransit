from abc import ABC, abstractmethod
import pandas as pd


class DataReader(ABC):

    @abstractmethod
    def read_world_clock_state(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_train_route_state(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_train_runtime_state(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_station_runtime_state(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_train_configuration(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_rail_segments_configuration(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_station_configuration(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_passenger_itinerary(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_passenger_route_state(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_passenger_runtime_state(self) -> pd.DataFrame:
        raise NotImplementedError()

    @abstractmethod
    def read_rail_segment_runtime_state(self) -> pd.DataFrame:
        raise NotImplementedError()
