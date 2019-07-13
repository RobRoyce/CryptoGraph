#!/usr/bin/env python
""" Provides an interface to external Crypto Exchange Markets (CEM).

Exchange is the base class and prototype for CEM API's.
"""
import abc


class Exchange(abc.ABC):
    @abc.abstractmethod
    def __init__(self, auth=None):
        pass

    @abc.abstractmethod
    def candles(self, product_id, start, end, granularity):
        pass

    @abc.abstractmethod
    def ticker(self):
        pass
