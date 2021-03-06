import unittest

import pystatsd

class TestPystatsd(unittest.TestCase):

    def test_counter_increment(self):
        pystatsd.increment(stat="foo.bar")
        pystatsd.increment(stat="foo.bar", delta=10)
        pystatsd.increment(stat="foo.bar", rate=0.5)

    def test_counter_decrement(self):
        pystatsd.decrement(stat="bar.baz")
        pystatsd.decrement(stat="foo.bar", delta=130)
        pystatsd.decrement(stat="bar.baz", rate=0.5)

    def test_gauge_increment(self):
        pystatsd.increment(stat="foo.bar", gauge=True)
        pystatsd.increment(stat="foo.bar", delta=10, gauge=True)
        pystatsd.increment(stat="foo.bar", rate=0.5, gauge=True)

    def test_gauge_decrement(self):
        pystatsd.decrement(stat="bar.baz", gauge=True)
        pystatsd.decrement(stat="foo.bar", delta=130, gauge=True)
        pystatsd.decrement(stat="bar.baz", rate=0.5, gauge=True)

    def test_gauge_set(self):
        pystatsd.set(stat="my.gauge", value=4000)
        pystatsd.set(stat="my.gauge", value=4100, rate=0.1)

    def test_timing(self):
        pystatsd.timing(stat="my.timer", value=400)

    def test_timing_context_manager(self):
        with pystatsd.Timer('my.timer'):
            for i in range(1, 1000):
                pass

    @pystatsd.Timer('my.timer')
    def test_timing_decorator(self):
        for i in range(1, 1000):
            pass

    def test_singleton(self):
        c1 = pystatsd.Client()
        c2 = pystatsd.Client()

        assert(c1 is c2)

    if __name__ == '__main__':
        unittest.main()
