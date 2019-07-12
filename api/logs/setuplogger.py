import os
import logging
from datetime import datetime

import pytz

if not os.path.exists('logs/archive'):
    try:
        os.makedirs('logs/archive')
    except OSError as err:
        raise err

class Logger:
    def __init__(self):
        fmt = '%(levelname)s %(asctime)s ~ %(name)s.%(funcName)s(): %(message)s'
        formatter = logging.Formatter(fmt=fmt)
        ds = self.__datestamp()
        handler = logging.FileHandler(
            os.path.join('logs/archive/', 'log-{}'.format(ds)))
        handler.setFormatter(formatter)
        self._log = logging.getLogger('root')
        self._log.setLevel(logging.DEBUG)
        self._log.addHandler(handler)

    def __datestamp(self):
        TZ = pytz.timezone('US/Pacific')
        return datetime(2020, 1,1).now(tz=TZ).date()

    def critical(self, msg):
        self._log.critical(msg)

    def debug(self, msg):
        self._log.debug(msg)

    def error(self, msg):
        self._log.error(msg)

    def info(self, msg):
        self._log.info(msg)

    def warn(self, msg):
        self._log.warn(msg)

logger = Logger()
