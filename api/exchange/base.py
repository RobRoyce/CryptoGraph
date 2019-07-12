#!/usr/bin/env python
""" Provides an interface to external Crypto Exchange Markets (CEM).

Exchange is the base class and prototype for CEM API's.
"""
import abc


class Exchange(abc.ABC):
    def __init__(self, auth=None):
        """Returns new Exchange object."""
        raise NotImplementedError

    @abc.abstractmethod
    def candles(self, product_id, start, end, granularity):
        raise NotImplementedError

    @abc.abstractmethod
    def ticker(self):
        raise NotImplementedError
