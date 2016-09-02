# pystatsd.py

# Modified from the original version by:
# Steve Ivy <steveivy@gmail.com>
# http://monkinetic.com
# https://github.com/sivy/pystatsd/blob/master/pystatsd

# Changelog:
# * Renamed pystatsd.Client to _StatsClient
# * Introduced singleton Client wrapper around StatsClient
# * Added `one-liner` API
# * Removed increment / decrement from _StatsClient as they were unused.

import logging
import socket
import random
import time

import os


# Public API

def increment(stat, delta=1, rate=1):
    """Increments the given counter by the delta provided (1 by default).

       Optionally the caller can specify both the rate for the increment (default is 1)
       as well as whether or not to treat the given stat as a gauge"""
    Client().increment(stat, delta, rate)

def decrement(stat, delta=1, rate=1):
    """Decrements the given counter by the delta provided (1 by default).

       Optionally the caller can specify both the rate for the decrement (default is 1)
       as well as whether or not to treat the given stat as a gauge"""
    Client().decrement(stat, delta, rate)

def set(stat, value, rate=1):
    """Sets the given gauge to the value provided.

       Optionally the caller can specify the rate for the set operation (default is 1)"""
    Client().set(stat, value, rate)

def timing(stat, value):
    """Set timing stat to the value provided."""
    Client().timing(stat, value)

class _Singleton(type):
    _instance = None
    def __call__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super(_Singleton, self).__call__(*args, **kwargs)
        return self._instance

class Client(object):
    """Singleton wrapper around _StatsClient.

       API matches that of the one-liner API to support use-cases where object references need to be shared."""
    __metaclass__ = _Singleton

    def __init__(self):
        host = os.getenv('STATSD_HOST', 'localhost')
        port = int(os.getenv('STATSD_PORT', '8125'))
        prefix = os.getenv('STATSD_PREFIX', "")
        self.client = _StatsClient(host, port, prefix=prefix)

    def increment(self, stat, delta=1, rate=1):
        """Increments the given counter by the delta provided (1 by default).

           Optionally the caller can specify both the rate for the increment (default is 1)
           as well as whether or not to treat the given stat as a gauge"""
	self.client.update_stats(stat, delta, rate)

    def decrement(self, stat, delta=1, rate=1):
        """Decrements the given counter by the delta provided (1 by default).

           Optionally the caller can specify both the rate for the decrement (default is 1)
           as well as whether or not to treat the given stat as a gauge"""
	self.client.update_stats(stat, -1 * delta, rate)

    def set(self, stat, value, rate=1):
        """Sets the given gauge to the value provided.

           Optionally the caller can specify the rate for the set operation (default is 1)"""
        self.client.gauge(stat, value, rate)

    def timing(self, stat, value):
        """Set timing stat to the value provided."""
        self.client.timing(stat, value)

# Private API

# Sends statistics to the stats daemon over UDP
# Renamed from the original pystatsd.Client class.
class _StatsClient(object):
    """ Internal helper class derived from sivy/pystatsd. """
    def __init__(self, host='localhost', port=8125, prefix=None):
        """
        Create a new Statsd client.
        * host: the host where statsd is listening, defaults to localhost
        * port: the port where statsd is listening, defaults to 8125

        >>> from pystatsd import statsd
        >>> stats_client = statsd.Statsd(host, port)
        """
        self.host = host
        self.port = int(port)
        self.addr = (socket.gethostbyname(self.host), self.port)
        self.prefix = prefix
        self.log = logging.getLogger("pystatsd.client")
        self.log.addHandler(logging.StreamHandler())
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def timing_since(self, stat, start, sample_rate=1):
        """
        Log timing information as the number of microseconds since the provided time float
        >>> start = time.time()
        >>> # do stuff
        >>> statsd_client.timing_since('some.time', start)
        """
        self.timing(stat, int((time.time() - start) * 1000000), sample_rate)

    def timing(self, stat, time, sample_rate=1):
        """
        Log timing information for a single stat
        >>> statsd_client.timing('some.time',500)
        """
        stats = {stat: "%f|ms" % time}
        self.send(stats, sample_rate)

    def gauge(self, stat, value, sample_rate=1):
        """
        Log gauge information for a single stat
        >>> statsd_client.gauge('some.gauge',42)
        """
        stats = {stat: "%f|g" % value}
        self.send(stats, sample_rate)

    def update_stats(self, stats, delta, sample_rate=1):
        """
        Updates one or more stats counters by arbitrary amounts
        >>> statsd_client.update_stats('some.int',10)
        """
        if not isinstance(stats, list):
            stats = [stats]

        data = dict((stat, "%s|c" % delta) for stat in stats)
        self.send(data, sample_rate)

    def send(self, data, sample_rate=1):
        """
        Squirt the metrics over UDP
        """

        if self.prefix:
            data = dict((".".join((self.prefix, stat)), value) for stat, value in data.items())

        if sample_rate < 1:
            if random.random() > sample_rate:
                return
            sampled_data = dict((stat, "%s|@%s" % (value, sample_rate))
                                for stat, value in data.items())
        else:
            sampled_data = data

        for stat, value in sampled_data.items():
            self.udp_send(bytes(bytearray("%s:%s" % (stat, value), "utf-8")))

    def udp_send(self, blob):
        try:
            self.udp_sock.sendto(blob, self.addr)
        except:
            self.log.exception("unexpected error")

    def __repr__(self):
        return "<pystatsd.statsd.Client addr=%s prefix=%s>" % (self.addr, self.prefix)
