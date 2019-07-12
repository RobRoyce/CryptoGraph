class Granularity:
    def __init__(self, *args):
        self.values = list(*args)
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
