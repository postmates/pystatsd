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
import datetime
from functools import wraps

import os


# Public API

def increment(stat, delta=1, rate=1, gauge=False):
    """Increments the given counter by the delta provided (default: 1).

       Optionally the caller can specify the rate for the decrement (default: 1) as
       well as whether to treat the stat as a gauge (default: False)."""
    Client().increment(stat, delta, rate, gauge)

def decrement(stat, delta=1, rate=1, gauge=False):
    """Decrements the given counter by the delta provided (default: 1).

       Optionally the caller can specify the rate for the decrement (default: 1) as
       well as whether to treat the stat as a gauge (default: False)."""
    Client().decrement(stat, delta, rate, gauge)

def set(stat, value, rate=1):
    """Sets the given gauge to the value provided.

       Optionally the caller can specify the rate for the set operation (default: 1)."""
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

class Timer(object):
    """A context manager/decorator for Client.timing()."""

    def __init__(self, stat, rate=1):
        self.stat = stat
        self.rate = rate
        self.ms = None
        self._sent = False
        self._start_time = None

    def __call__(self, f):
        """Thread-safe timing function decorator."""
        @wraps(f)
        def _wrapped(*args, **kwargs):
            start_time = _utcnow()
            try:
                return_value = f(*args, **kwargs)
            finally:
                elapsed_time_ms = 1000.0 * (_utcnow() - start_time).total_seconds()
                Client().timing(self.stat, elapsed_time_ms, self.rate)
            return return_value
        return _wrapped

    def __enter__(self):
        return self.start()

    def __exit__(self, typ, value, tb):
        self.stop()

    def start(self):
        self.ms = None
        self._sent = False
        self._start_time = _utcnow()
        return self

    def stop(self, send=True):
        if self._start_time is None:
            raise RuntimeError('Timer has not started.')
        dt = (_utcnow() - self._start_time).total_seconds()
        self.ms = 1000.0 * dt  # Convert to milliseconds.
        if send:
            self.send()
        return self

    def send(self):
        if self.ms is None:
            raise RuntimeError('No data recorded.')
        if self._sent:
            raise RuntimeError('Already sent data.')
        self._sent = True
        Client().timing(self.stat, self.ms, self.rate)

class Client(object):
    """Singleton wrapper around _StatsClient.

       API matches that of the one-liner API to support use-cases where object references need to be shared."""
    __metaclass__ = _Singleton

    def __init__(self):
        host = os.getenv('STATSD_HOST', 'localhost')
        port = int(os.getenv('STATSD_PORT', '8125'))
        prefix = os.getenv('STATSD_PREFIX', "")
        self.client = _StatsClient(host, port, prefix=prefix)

    def increment(self, stat, delta=1, rate=1, gauge=False):
        """Increments the given counter by the delta provided (default: 1).

           Optionally the caller can specify the rate for the decrement (default is 1) as
           well as whether to treat the stat as a gauge (default: False)."""
        self.client.update_stats(stat, delta, rate, gauge)

    def decrement(self, stat, delta=1, rate=1, gauge=False):
        """Decrements the given counter by the delta provided (default: 1).

           Optionally the caller can specify the rate for the decrement (default: 1) as
           well as whether to treat the stat as a gauge (default: False)."""
        self.client.update_stats(stat, -1 * delta, rate, gauge)

    def set(self, stat, value, rate=1):
        """Sets the given gauge to the value provided.

           Optionally the caller can specify the rate for the set operation (default: 1)"""
        self.client.gauge(stat, value, rate)

    def timing(self, stat, value, rate=1):
        """Set timing stat to the value provided."""
        self.client.timing(stat, value, rate)

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
        set_gauge = "%s|g" % value
        if value >= 0:
            stats = {stat: set_gauge}
        else:
            payload = ["0|g", set_gauge],
            stats = {stat: payload}

        self.send(stats, sample_rate)

    def update_stats(self, stats, delta, sample_rate=1, gauges=False):
        """
        Updates one or more stats counters by arbitrary amounts
        >>> statsd_client.update_stats('some.int',10)
        """
        if not isinstance(stats, list):
            stats = [stats]

        if gauges:
            prefix = '+' if delta and delta >= 0 else ''
            data = dict((stat, "%s%s|g" % (prefix,delta)) for stat in stats)
        else:
            data = dict((stat, "%s|c" % delta) for stat in stats)
        self.send(data, sample_rate)

    def render_datum(self, stat, value_or_list, sample_rate=1):
        value_list = value_or_list if isinstance(value_or_list, list) else [value_or_list]
        string = '\n'.join([self.render_data(stat, value, sample_rate) for value in value_list])
        return bytes(bytearray("%s:%s" % (stat, string), "utf-8"))

    def render_data(self, stat, value, sample_rate=1):
        if sample_rate < 1:
            sample_data = "%s|@%s" % (value, sample_rate)
        else:
            sample_data = value

        return "%s:%s" % (stat, sample_data)

    def send(self, data, sample_rate=1):
        """
        Squirt the metrics over UDP
        """

        if self.prefix:
            data = dict((".".join((self.prefix, stat)), value) for stat, value in data.items())

        if sample_rate < 1:
            if random.random() > sample_rate:
                return

        for stat, value in data.items():
            self.udp_send(self.render_datum(stat, value, sample_rate))

    def udp_send(self, blob):
        try:
            self.udp_sock.sendto(blob, self.addr)
        except:
            self.log.exception("unexpected error")

    def __repr__(self):
        return "<pystatsd.statsd.Client addr=%s prefix=%s>" % (self.addr, self.prefix)

def _utcnow():
        return datetime.datetime.utcnow()
