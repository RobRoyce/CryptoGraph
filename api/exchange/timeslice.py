import time
from time import mktime
from datetime import timedelta
from datetime import datetime
from math import ceil
from dateutil import parser


class TimeSlice:
    """TimeSlice is a utility for standardizing timestamps accross the codebase.

    The end goal is to work exclusively with datetime objects, but to be
    able to convert back and forth with ISO 8601 and seconds seamlessly.
    """

    def __init__(self):
        pass

    @staticmethod
    def convert_datetime(start: datetime, end: datetime = False,
                         iso8601: bool = False):
        """Converts a datetime object into its epoch time (in seconds) or
        an iso8601 string

        Keyword arguments:
        start -- a datetime.datetime object
        end -- optional datetime.datetime object
        iso8601 -- set to True for iso8601 formated string instead of seconds

        Returns:
        <float> or <float>, <float>    or...
        <str> or <str>, <str>
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
    def convert_iso_str(start: str, end: str = False, seconds: bool = False):
        """Converts an iso8601 string into a datetime object or a float as
        seconds since epoch.

        Keyword arguments:
        start -- an iso8601 string
        end -- optional iso8601 string
        seconds -- set to True for seconds since epoch instead of datetime

        Returns:
        <datetime> or <datetime>, <datetime>    or...
        <float> or <float>, <float>
        """
        if end:
            try:
                _start = parser.parse(start)
                _end = parser.parse(end)
            except Exception as err:
                msg = 'attempting to parse {} and {}\n{}'.format(
                    _start, _end, err)
                raise Exception(msg)

            if seconds:
                return mktime(_start.timetuple()), mktime(_end.timetuple())
            return _start, _end

        if seconds:
            return mktime(parser.parse(start).timetuple())
        return parser.parse(start)

    @staticmethod
    def convert_seconds(start: float, end: float = False,
                        iso8601: bool = False):
        """Converts seconds since epoch into utc datetime or utc iso8601 string

        Keyword arguments:
        start -- a float as seconds since epoch
        end -- optional float as seconds since epoch
        iso8601 -- set to True for iso8601 formated string instead of datetime

        Returns:
        <datetime> or <datetime>, <datetime>    or...
        <str> or <str>, <str>
        """
        if end:
            _start = datetime.utcfromtimestamp(start)
            _end = datetime.utcfromtimestamp(end)

            if iso8601:
                return _start.isoformat(), _end.isoformat()
            return _start, _end

        _start = datetime.utcfromtimestamp(start)
        if iso8601:
            return _start.isoformat()
        return _start

    @staticmethod
    def time_slice(start: datetime, end: datetime,
                   granularity: int, iso8601: bool = False) -> list:
        """Returns a list whose elements are pairs (slices) of datetime deltas.
        Ex: `[[datetime1, datetime2], [datetime3, datetime4], ...]`

        Note: The slices are returned with the assumption that each
        call to an Exchange will return a list with no more than exactly
        300 candles at once. At the moment, this is something that Coinbase
        has instituted and explicity states in their API documentation. I don't
        see a way around this, and I might need to rewrite this function
        for other Exchanges in the future. Be aware that the range of the
        slices might appear arbitrary. In fact, each range will equal the
        size of the granularity times 300.

        Keyword arguments:
        start -- a datetime.datetime object
        end -- a datetime.datetime object
        granularity -- an integer representing granularity in seconds
        iso8601 -- True to return iso8601 formated string rather than datetime

        Returns:
        [[<datetime>,<datetime>], ...]  or...
        [[<str>,<str>], ...]
        """
        errors = [
            (start > end),
            (not isinstance(start, datetime)),
            (not isinstance(end, datetime))
        ]
        if any(errors):
            raise Exception('start: {}, end: {}, granularity: {}'.format(
                start, end, granularity))

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
