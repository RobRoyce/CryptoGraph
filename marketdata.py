import sys
import random
import logging

from datetime import datetime

from api.cbexchange import Coinbase
from api.coinbase.exceptions import *
from api.exchange.base import Exchange
from api.exchange.candle import Candle
from api.exchange.timeslice import TimeSlice
from api.logs.setuplogger import logger


class MarketData():
    def __init__(self, ex: Exchange) -> None:
        self.__validate(ex, Exchange)
        self._exchange = ex
        self._event_log = logging.getLogger('root.{}'.format(
            self.__class__.__name__))
        self._event_log.debug('Initializing...')

    def available_granularity(self):
        """Determines available and valid granularities in active exchange"""
        return self._exchange.available_granularity()

    def available_trade_pairs(self) -> list:
        """Determines which currencies are available in active exchange"""
        return self._exchange.valid_product_ids()

    def candles(self, product_id, start, end, granularity):
        """Return a pack of `Candle`'s based on numerous criteria

        Keyword arguments:
        product_id -- must be a valid product_id in the current exchange
        start -- must be a valid ISO 8601 timestamp
        end -- must be a valid ISO 8601 timestamp
        granularity -- must be a valid granularity in the current exchange
        '"""
        try:
            data = self._exchange.candles(product_id, start, end, granularity)
        except ExchangeError as err:
            self._event_log.exception(err)
            raise err

        candles = []
        for item in data:
            candles.append(dict(zip(Candle.get_labels(), item)))
        return candles

    def es_candle_generator(self, index, product_id, start, end, granularity):
        failed_attempts = 0
        try:
            _candles = self.candles(product_id, start, end, granularity)
        except ExchangeError as err:
            self._event_log.exception(err)
            raise err
        except Exception as err:
            self._event_log.exception(err)
            raise err

        if _candles:
            for _candle in _candles:
                yield {
                    'index': {'_index': index},
                    'time': _candle['time'],
                    'product_id': product_id,
                    'high': _candle['high'],
                    'low': _candle['low'],
                    'open': _candle['open'],
                    'close': _candle['close'],
                    'volume': _candle['volume']
                    }
        else:
            if failed_attempts >= 10:
                msg = 'Too many failed attempts. Invalid range or granularity'
                raise InvalidArgument(msg)
            failed_attempts = failed_attempts + 1

    @staticmethod
    def package_candles(data):
        """Takes in raw candle data and returns a list of Candle objects"""
        box = []
        for item in data:
            _candle = Candle(*item)
            box.append(_candle)
        return box

    def slices(self, product_id: str, start: datetime, end: datetime, granularity: int) -> list:
        """Returns a list of time sliced candle data based on time range and granularity"""
        time_slice = TimeSlice.time_slice(start, end, granularity, iso8601=True)
        slices = []
        slice_count = 0
        failed_attempts = 0

        for _start, _end in time_slice:
            slice_count = slice_count + 1

            try:
                _candles = self.candles(product_id, _start, _end, granularity)
            except ExchangeError as err:
                raise err

            success = len(_candles) > 0
            self._event_log.debug('Candles pulled successfully: {}'.format(success))

            if success:
                slices.append(_candles)
                s = 'Candles pulled: %i\nSample candle: %s'
                self._event_log.debug(s, len(_candles), _candles[0])
            else:
                if failed_attempts > 2:
                    return slices
                failed_attempts = failed_attempts + 1

        return slices

    def ticker(self, product_id):
        return self._exchange.ticker(product_id)

    @staticmethod
    def __validate(type1, type2):
        """Raises ExchangeError if the types are not equivalent"""
        if not isinstance(type1, type2):
            raise ExchangeError('Type mismatch {}'.format((type1, type2)))

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass

if __name__ == '__main__':
    exchange = Coinbase()
    md = MarketData(exchange)
    print(md.ticker('ETH-USD'))
