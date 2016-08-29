from threading import Thread
from multiprocessing import Queue
from enum import Enum

import os
import statsd

# Public API

def increment(stat, delta=1, rate=1, gauge=False):
    """Increments the given counter by the delta provided (1 by default).

       Optionally the caller can specify both the rate for the increment (default is 1)
       as well as whether or not to treat the given stat as a gauge"""
    Client().increment(stat, delta, rate, gauge)

def decrement(stat, delta=1, rate=1, gauge=False):
    """Decrements the given counter by the delta provided (1 by default).

       Optionally the caller can specify both the rate for the decrement (default is 1)
       as well as whether or not to treat the given stat as a gauge"""
    Client().decrement(stat, delta, rate, gauge)

def set(stat, value, rate=1):
    """Sets the given gauge to the value provided.

       Optionally the caller can specify the rate for the set operation (default is 1)"""
    Client().set(stat, value, rate)

def distinct(stat, value):
    """Add value to the set identified by stat, if it doesn't already exist"""
    Client().distinct(state, value)

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
    __metaclass__ = _Singleton

    def __init__(self):
        self._worker = _StatsdWorker()
        self._worker.run()

    def enqueue(self, action):
        self._worker.enqueue(action)

    def increment(self, stat, delta=1, rate=1, gauge=False):
        """Increments the given counter by the delta provided (1 by default).

           Optionally the caller can specify both the rate for the increment (default is 1)
           as well as whether or not to treat the given stat as a gauge"""
        kind = _StatsdOp.delta
        action = _StatsdAction(kind=kind, stat=stat, val=delta, rate=rate, gauge=gauge)
        self.enqueue(action)

    def decrement(self, stat, delta=1, rate=1, gauge=False):
        """Decrements the given counter by the delta provided (1 by default).

           Optionally the caller can specify both the rate for the decrement (default is 1)
           as well as whether or not to treat the given stat as a gauge"""
        kind = _StatsdOp.delta
        action = _StatsdAction(kind=kind, stat=stat, val=-1*delta, rate=rate, gauge=gauge)
        self.enqueue(action)

    def set(self, stat, value, rate=1):
        """Sets the given gauge to the value provided.

           Optionally the caller can specify the rate for the set operation (default is 1)"""
        kind = _StatsdOp.set
        action = _StatsdAction(kind=kind, stat=stat, val=value, rate=rate, gauge=True)
        self.enqueue(action)

    def distinct(self, stat, value):
        """Add value to the set identified by stat, if it doesn't already exist"""
        kind = _StatsdOp.distinct
        action = _StatsdAction(kind=kind, stat=stat, val=value)
        self.enqueue(action)

    def timing(self, stat, value):
        """Set timing stat to the value provided."""
        kind = _StatsdOp.timing
        action = _StatsdAction(kind=kind, stat=stat, val=value)
        self.enqueue(action)

# Private API

def _worker_loop(obj):
    while True:
        action = obj.dequeue()
        kind = action.kind
        stat = obj.prefix + action.stat
        val = action.val
        gauge = action.gauge
        rate = action.rate

        if kind == _StatsdOp.stop:
            break
        elif kind == _StatsdOp.delta:
            obj.delta(stat, val, rate, gauge)
        elif kind == _StatsdOp.timing:
            obj.timing(stat, val, rate)
        elif (kind == _StatsdOp.set) and gauge:
            obj.gauge_set(stat, val, rate)
        elif action.kind == _StatsdOp.distinct:
            obj.distinct(stat, val)

class _StatsdOp(Enum):
    delta = 1
    set = 2
    distinct = 3
    timing = 4
    stop = 5

class _StatsdAction:
    def __init__(self, kind, stat, val=1, rate=1, gauge=False):
        self.kind = kind
        self.stat = stat
        self.val = val
        self.gauge = gauge
        self.rate = rate

class _StatsdWorker:

    def __init__(self):
        self.queue = Queue()

        host = os.getenv('STATSD_HOST', 'localhost')
        port = int(os.getenv('STATSD_PORT', '8125'))
        prefix = os.getenv('STATSD_PREFIX', "")

        # We set prefix here as StatsdClient appends a "." after all prefix
        self.prefix = prefix
        self.conn = statsd.StatsClient(host, port)
        self.p = None

    def run(self):
        if (not self.p):
            self.p = Thread(target=_worker_loop, args=(self,))
            self.p.daemon = True
            self.p.start()

    def stop(self):
        kind = _StatsdOp.stop
        action = _StatsdAction(kind=kind, stat="", val=10)
        self.enqueue(action)
        self.p.join()

    def enqueue(self, statsdAction):
        self.queue.put(statsdAction)

    def dequeue(self):
        return self.queue.get(True, None)

    def increment(self, stat, delta=1, rate=1, gauge=False):
        if not gauge:
            self.conn.incr(stat, delta, rate)
        else:
            self.conn.gauge(stat, delta, rate, True)

    def decrement(self, stat, delta=1, rate=1, gauge=False):
        if not gauge:
            self.conn.decr(stat, delta, rate)
        else:
            self.conn.gauge(stat, delta, rate, True)

    def delta(self, stat, delta=1, rate=1, gauge=False):
        if delta >= 0:
            self.increment(stat, delta, rate, gauge)
        else:
            self.decrement(stat, delta, abs(delta), gauge)

    def gauge_set(self, stat, val, rate):
        self.conn.gauge(stat, val, rate)

    def timing(self, stat, delta, rate=1):
        self.conn.timing(stat, delta, rate)

    def distinct(self, stat, value):
        self.conn.set(stat, value)
