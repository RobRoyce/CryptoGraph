'''Example usage of CryptoGraph with ElasticSearch.

Note: ElasticSearch must be running on your computer.
You will find log data in logs/archive/log-[date]. The logger can be used
from any module within the CryptoGraph root, simply by:
    `from api.logs.setuplogger import logger`
    `my_log = logging.getLogger('root.[your.moule.here]')`
'''
import datetime
import logging
import time

from elasticsearch import Elasticsearch

from api.cbexchange import Coinbase
from api.coinbase.exceptions import *
from api.exchange.timeslice import TimeSlice
from api.logs.setuplogger import logger
from marketdata import MarketData



if __name__ == '__main__':

    event_log = logging.getLogger('root.demo')
    event_log.debug('{} started...'.format(__name__))
    exchange = Coinbase()


    es = Elasticsearch()
    index = 'test-{}'.format(str(int(time.time()))[-4:])
    print(index)
    es_settings = {
        'settings': {},
        'mappings': {
            'properties': {
                'time': {'type': 'date', 'format': 'epoch_second'},
                'high': {'type': 'float'},
                'low': {'type': 'float'},
                'open': {'type': 'float'},
                'close': {'type': 'float'},
                'volume': {'type': 'float'},
                'product_id': {'type': 'keyword'}
            }
        }
    }
    es.indices.create(index=index, body=es_settings)

    md = MarketData(exchange)
    products = ['BTC-USD']
    granularities = md.available_granularity().values
    start = datetime.datetime(year=2019, month=1, day=1)
    end = datetime.datetime(year=2019, month=6, day=1)

    for granularity in granularities:
        slices = TimeSlice.time_slice(start, end, granularity)
        for product_id in products:
            for _start, _end in slices:
                try:
                    Elasticsearch.bulk(es, md.es_candle_generator(
                        index, product_id, _start, _end, granularity))
                except InvalidArgument as err:
                    event_log.exception(err)
                    raise err
                event_log.debug('%s to %s @ %s DONE...',
                                _start, _end, granularity)
