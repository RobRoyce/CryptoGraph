class Granularity:
    """A class for storing valid time intervals within an Exchange

    Supports:
    len(my_granularity),
    if my_granularity in x:
    iter(my_granularity)
    next(my_granularity)
    str(my_granularity)
    """

    def __init__(self, *granularities):
        """A class for storing valid time intervals within an Exchange

        Keyword arguments:
        granularities -- a Tuple with all of the valid granularities
        """
        self.values = list(*granularities)
        self.__index = 0

    def min(self):
        return min(self.values)

    def max(self):
        return max(self.values)

    def __contains__(self, member):
        return member in self.values

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index == len(self.values):
            raise StopIteration
        self.__index = self.__index + 1
        return self.values[self.__index]

    def __str__(self):
        return str(self.values)
