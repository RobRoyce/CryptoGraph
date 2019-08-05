import pprint
from collections import Iterable


class Candle(Iterable):
    def __init__(self, *args):
        self.time = args[0]
        self.low = args[1]
        self.high = args[2]
        self.open = args[3]
        self.close = args[4]
        self.volume = args[5]
        self.labels = ['time', 'low', 'high', 'open', 'close', 'volume']

        self.values = [
            self.time, self.low, self.high, self.open, self.close, self.volume
        ]

        self.__index = 0

    def key_value_pair(self):
        return dict(zip(self.labels, self.values))

    @staticmethod
    def get_labels() -> list:
        return ['time', 'low', 'high', 'open', 'close', 'volume']

    def labeled_pairs(self):
        return list(zip(self.labels, self.values))

    def prettify(self):
        return pprint.pformat(self.labeled_pairs())

    def __contains__(self, member):
        return member in self.labels or member in self.values

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index == len(self.values):
            raise StopIteration
        self.__index = self.__index + 1
        return self.labeled_pairs()[self.__index - 1]

    def __str__(self):
        return self.prettify()
