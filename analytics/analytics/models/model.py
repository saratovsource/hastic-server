import utils

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd
import math

ModelCache = dict

class Segment(dict):

    self.__percent_of_nans = 0

    def __init__(self, dataframe: pd.DataFrame, segment_map: dict):
        super(Segment, self).__init__(**segment_map)
        self.__dict__ = self
        self.update(segment_map)
        self.from = timestamp_to_index(dataframe, pd.to_datetime(self.from, unit='ms'))
        self.to = timestamp_to_index(dataframe, pd.to_datetime(self.to, unit='ms'))
        self.data = dataframe['value'][start: end + 1]
        self.length = abs(self.to - self.from)

    @property
    def percent_of_nans:
        if not self.__percent_of_nans:
            self.__percent_of_nans = self.data.isnull().sum() / len(self.data)
        return self.__percent_of_nans

    def convert_nan_to_zero(self):
        nan_list = utils.find_nan_indexes(self.data)
        self.data = utils.nan_to_zero(self.data, nan_list)

class Model(ABC):

    @abstractmethod
    def do_fit(self, dataframe: pd.DataFrame, segments: list, cache: Optional[ModelCache]) -> None:
        pass

    @abstractmethod
    def do_detect(self, dataframe: pd.DataFrame) -> list:
        pass

    def fit(self, dataframe: pd.DataFrame, segments: list, cache: Optional[ModelCache]) -> ModelCache:
        if type(cache) is ModelCache:
            self.state = cache

        max_length = 0
        labeled = []
        deleted = []
        for segment_map in segments:
            if segment_map['labeled'] or segment_map['deleted']:
                segment = Segemnt(dataframe, segment_map)
                if segment.percent_of_nans > 0.1 or len(segment.data) == 0:
                    continue
                if segment.percent_of_nans > 0:
                    segment.convert_nan_to_zero()

                max_length = max(segment.length, max_length)
                if segment.labeled: labeled.append(segment)
                if segment.deleted: deleted.append(segment)
                    

        self.state['WINDOW_SIZE'] = math.ceil(max_length / 2) if max_length else 0
        self.do_fit(dataframe, labeled, deleted)
        return self.state

    def detect(self, dataframe: pd.DataFrame, cache: Optional[ModelCache]) -> dict:
        if type(cache) is ModelCache:
            self.state = cache

        result = self.do_detect(dataframe)
        # TODO: convert from ns to ms more proper way (not dividing by 10^6)
        segments = [(
            dataframe['timestamp'][x - 1].value / 1000000,
            dataframe['timestamp'][x + 1].value / 1000000
        ) for x in result]

        return {
            'segments': segments,
            'cache': self.state
        }
