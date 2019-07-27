import unittest
from datetime import datetime
from timeslice import TimeSlice

class TestTimeSlice(unittest.TestCase):

    def test_convert_datetime(self):
        ts = TimeSlice()
        start = datetime(2020, 1,1)
        end = datetime(2030, 1, 1)

        start_in_secs = ts.convert_datetime(start)
        self.assertEqual(start_in_secs, 1577865600.0)

        start_in_iso8601 = ts.convert_datetime(start, iso8601=True)
        self.assertEqual(start_in_iso8601, '2020-01-01T00:00:00')

        start_in_secs, end_in_secs = ts.convert_datetime(start, end)
        self.assertEqual(start_in_secs, 1577865600.0)
        self.assertEqual(end_in_secs, 1893484800.0)

        start_in_iso8601, end_in_iso8601 = ts.convert_datetime(start, end, True)
        self.assertEqual(start_in_iso8601, '2020-01-01T00:00:00')
        self.assertEqual(end_in_iso8601, '2030-01-01T00:00:00')


if __name__ == '__main__':
    unittest.main()
