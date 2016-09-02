import unittest

import statsd
import pystatsd

class TestPystatsd(unittest.TestCase):

    def test_no_exceptions_with_bad_types(self):
        """Asserts that StatsClients are resilient to type mismatches."""
        conn = statsd.StatsClient()
        conn.incr("foo", "12")
        conn.incr("foo.bar", 12, "-100")
        conn.incr(733, 12, 1.0)
        conn.incr("foo.gauge", 12, 1.0)

        conn.gauge(12, 40)
        conn.gauge("foo.bar", "adsfasdf")
        conn.gauge("foo.bar", 10, "-100")

    def test_counter_increment(self):
        pystatsd.increment(stat="foo.bar")
        pystatsd.increment(stat="foo.bar", delta=10)
        pystatsd.increment(stat="foo.bar", rate=0.5)

    def test_counter_decrement(self):
        pystatsd.decrement(stat="bar.baz")
	pystatsd.decrement(stat="foo.bar", delta=130)
        pystatsd.decrement(stat="bar.baz", rate=0.5)

    def test_gauge_set(self):
        pystatsd.set(stat="my.gauge", value=4000)
        pystatsd.set(stat="my.gauge", value=4100, rate=0.1)

    def test_timing(self):
        pystatsd.timing(stat="my.timer", value=400)

    def test_singleton(self):
        c1 = pystatsd.Client()
        c2 = pystatsd.Client()
        assert(c1 is c2)

    if __name__ == '__main__':
        unittest.main()
