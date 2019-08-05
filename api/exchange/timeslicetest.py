import unittest
from datetime import datetime
from timeslice import TimeSlice


class TestTimeSlice(unittest.TestCase):
    def test_convert_datetime(self):
        ts = TimeSlice()
        start = datetime(2020, 1, 1)
        end = datetime(2030, 1, 1)

        # Start-only, seconds
        start_in_secs = ts.convert_datetime(start)
        self.assertEqual(start_in_secs, 1577865600.0)

        # Start-only, iso8601
        start_in_iso8601 = ts.convert_datetime(start, iso8601=True)
        self.assertEqual(start_in_iso8601, '2020-01-01T00:00:00')

        # Start-End, seconds
        start_in_secs, end_in_secs = ts.convert_datetime(start, end)
        self.assertEqual(start_in_secs, 1577865600.0)
        self.assertEqual(end_in_secs, 1893484800.0)

        # Start-End, iso8601
        start_in_iso8601, end_in_iso8601 = ts.convert_datetime(
            start, end, True)
        self.assertEqual(start_in_iso8601, '2020-01-01T00:00:00')
        self.assertEqual(end_in_iso8601, '2030-01-01T00:00:00')

        with self.assertRaises(AttributeError):
            ts.convert_datetime('random string')

    def test_convert_iso_str(self):
        ts = TimeSlice()
        start = '2020-01-01T00:00:00'
        end = '2030-01-01T00:00:00'

        # Start-only, datetime
        start_in_datetime = ts.convert_iso_str(start)
        self.assertEqual(start_in_datetime, datetime(2020, 1, 1))

        # Start-only, seconds
        start_in_seconds = ts.convert_iso_str(start, seconds=True)
        self.assertEqual(start_in_seconds, 1577865600.0)

        # Start-End, datetime
        start_in_datetime, end_in_datetime = ts.convert_iso_str(start, end)
        self.assertEqual(start_in_datetime, datetime(2020, 1, 1))
        self.assertEqual(end_in_datetime, datetime(2030, 1, 1))

        # Start-End, seconds
        start_in_seconds, end_in_seconds = ts.convert_iso_str(start, end, True)
        self.assertEqual(start_in_seconds, 1577865600.0)
        self.assertEqual(end_in_seconds, 1893484800.0)

        with self.assertRaises(ValueError):
            ts.convert_iso_str('random string')

        with self.assertRaises(TypeError):
            ts.convert_iso_str(datetime(2020, 1, 1))

    def test_convert_seconds(self):
        ts = TimeSlice()
        start = 1577865600.0
        end = 1893484800.0

        # Start-only, datetime
        start_in_datetime = ts.convert_seconds(start)
        self.assertEqual(start_in_datetime, datetime(2020, 1, 1))

        # Start-only, datetime, utc
        start_in_datetime = ts.convert_seconds(start, utc=True)
        self.assertEqual(start_in_datetime, datetime(2020, 1, 1, 8))

        # Start-only, iso8601
        start_in_iso8601 = ts.convert_seconds(start, iso8601=True)
        self.assertEqual(start_in_iso8601, '2020-01-01T00:00:00')

        # Start-only, iso8601, utc
        start_in_iso8601 = ts.convert_seconds(start, iso8601=True, utc=True)
        self.assertEqual(start_in_iso8601, '2020-01-01T08:00:00')

        # Start-End, datetime
        start_in_datetime, end_in_datetime = ts.convert_seconds(start, end)
        self.assertEqual(start_in_datetime, datetime(2020, 1, 1))
        self.assertEqual(end_in_datetime, datetime(2030, 1, 1))

        # Start-End, datetime, utc
        start_in_datetime, end_in_datetime = ts.convert_seconds(start,
                                                                end,
                                                                utc=True)
        self.assertEqual(start_in_datetime, datetime(2020, 1, 1, 8))
        self.assertEqual(end_in_datetime, datetime(2030, 1, 1, 8))

        # Start-only, iso8601
        start_in_iso8601, end_in_iso8601 = ts.convert_seconds(start,
                                                              end,
                                                              iso8601=True)
        self.assertEqual(start_in_iso8601, '2020-01-01T00:00:00')
        self.assertEqual(end_in_iso8601, '2030-01-01T00:00:00')

        # Start-only, iso8601, utc
        start_in_iso8601, end_in_iso8601 = ts.convert_seconds(start,
                                                              end,
                                                              iso8601=True,
                                                              utc=True)
        self.assertEqual(start_in_iso8601, '2020-01-01T08:00:00')
        self.assertEqual(end_in_iso8601, '2030-01-01T08:00:00')

        with self.assertRaises(TypeError):
            ts.convert_seconds('random string')

        with self.assertRaises(TypeError):
            ts.convert_seconds(datetime(2020, 1, 1))

    def test_time_slice(self):
        ts = TimeSlice()
        start = datetime(2020, 1, 1)
        end = datetime(2030, 1, 1)
        granularity = 5000

        # datetime
        ts_list = ts.time_slice(start, end, granularity)
        self.assertEqual(len(ts_list), 211)
        self.assertEqual(
            ts_list[0],
            [datetime(2020, 1, 1, 0, 0),
             datetime(2020, 1, 18, 8, 40)])
        self.assertEqual(
            ts_list[210],
            [datetime(2029, 12, 24, 20, 0),
             datetime(2030, 1, 1, 0, 0)])

        ts_list = ts.time_slice(start, end, granularity, True)
        self.assertEqual(len(ts_list), 211)
        self.assertEqual(ts_list[0],
                         ['2020-01-01T00:00:00', '2020-01-18T08:40:00'])
        self.assertEqual(ts_list[210],
                         ['2029-12-24T20:00:00', '2030-01-01T00:00:00'])


if __name__ == '__main__':
    unittest.main()
