import time
from time import mktime
from datetime import timedelta
from datetime import datetime
from math import ceil
from dateutil import parser


class TimeSlice():
    """TimeSlice is a utility for standardizing timestamps accross the codebase.

    The end goal is to work exclusively with datetime objects, but to be
    able to convert back and forth with ISO 8601 and seconds seamlessly.
    """
    def __init__(self):
        pass

    @staticmethod
    def convert_datetime(start: datetime, end: datetime=False, iso8601: bool=False) -> tuple:
        """ Returns a tuple with the parameters converted to seconds.

        Keyword arguments:
        start -- a datetime.datetime object
        end -- an optional datetime.datetime object
        iso8601 -- set to True if you want the times returned in ISO format
        """
        if end:
            if iso8601:
                _start = start.isoformat()
                _end = end.isoformat()
            else:
                _start = time.mktime(start.timetuple())
                _end = time.mktime(end.timetuple())
            return _start, _end
        else:
            if iso8601:
                _start = start.isoformat()
            else:
                _start = time.mktime(start.timetuple())
            return _start

    @staticmethod
    def convert_iso_str(iso_str, seconds=False):
        if seconds:
            return mktime(parser.parse(iso_str).timetuple())
        return parser.parse(iso_str)

    @staticmethod
    def convert_seconds(start: float, end: float=False, iso8601: bool=False):
        if end:
            _start = datetime.utcfromtimestamp(start)
            _end = datetime.utcfromtimestamp(end)

            if iso8601:
                return _start.isoformat(), _end.isoformat()
            else:
                return _start, _end
        else:
            _start = datetime.utcfromtimestamp(start)
            if iso8601:
                return _start.isoformat()
            else:
                return _start

    @staticmethod
    def get_range_from_delta(start, delta, iso8601=False):
        """Takes a datetime and a timedelta and returns two datetime's.
        """
        if isinstance(start, datetime):
            if delta.total_seconds() > 0:
                return start, start + delta
            else:
                return start + delta, start
        else:
            raise Exception('start must be datetime')

    @staticmethod
    def get_time_range_in_seconds(start, end):
        """ Returns a tuple with the parameters converted to seconds.

        Keyword argument:
        start -- a time in _ISO 8601_ for the start of the period
        end -- a time in __ISO 8601_ for the end of the period
        """
        _start = TimeSlice.convert_iso_str(start)
        _end = TimeSlice.convert_iso_str(end)
        return (_start, _end)

    @staticmethod
    def time_slice(start: datetime, end: datetime, granularity: int, iso8601: bool=False) -> list:
        """Returns a list of start and end times that will achieve the given granularity

        Keyword arguments:
        start -- a datetime.datetime object
        end -- a datetime.datetime object
        granularity -- an integer representing granularity in seconds
        """
        errors = [
            (start > end),
            (not isinstance(start, datetime)),
            (not isinstance(end, datetime))
        ]
        if any(errors):
            raise Exception('start: {}, end: {}, granularity: {}'.format(start, end, granularity))

        delta = (end - start)
        slice_size = granularity * 300
        slice_count = int(ceil(delta.total_seconds() / slice_size))
        slice_delta = timedelta(seconds=slice_size)
        slices = []
        _start = start
        for i in range(0, slice_count):
            if i == slice_count - 1:
                _end = end
            else:
                _end = _start + slice_delta

            if iso8601:
                slices.append([_start.isoformat(), _end.isoformat()])
            else:
                slices.append([_start, _end])
            _start = _end

        return slices
