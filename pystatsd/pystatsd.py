from threading import Thread
from multiprocessing import Queue
from enum import Enum

import statsd

# Public API

def increment(stat, delta=1, rate=1, gauge=False):
    kind = StatsdOp.delta
    action = StatsdAction(kind=kind, stat=stat, val=delta, rate=rate, gauge=gauge)
    _enqueue(action)

def decrement(stat, delta=1, rate=1, gauge=False):
    kind = StatsdOp.delta
    action = StatsdAction(kind=kind, stat=stat, val=-1*delta, rate=rate, gauge=gauge)

def set(stat, value, rate=1):
    kind = StatsdOp.gauge_set,
    action = StatsdAction(kind=kind, stat=stat, val=value, rate=rate, gauge=True)
    _enqueue(action)

def distinct(stat, value):
    kind = StatsdOp.distinct
    action = StatsdAction(kind=kind, stat=stat, val=value)
    _enqueue(action)

def timing(stat, value):
    kind = StatsdOp.timing
    action = StatsdAction(kind=kind, stat=stat, val=value)
    _enqueue(action)

# Private API

def _enqueue(action):
    __STATSD_WORKER__.enqueue(action)

def _worker_loop(obj):
    while True:
        action = obj.dequeue()
        kind = action.kind
        stat = action.stat
        val = action.val
        gauge = action.gauge
        rate = action.rate

        if kind == StatsdOp.delta:
            obj.delta(stat, val, rate, gauge)
        elif kind == StatsdOp.timing:
            obj.timing(stat, val, rate)
        elif (kind == StatsdOp.gauge_set) and gauge:
            obj.gauge_set(stat, val, rate)
        elif action.kind == StatsdOp.distinct:
            obj.distinct(stat, val)

class StatsdOp(Enum):
    delta = 1
    gauge_set = 2
    distinct = 3
    timing = 4

class StatsdAction:
    def __init__(self, kind, stat, val=1, rate=1, gauge=False):
        self.kind = kind
        self.stat = stat
        self.val = val
        self.gauge = gauge
        self.rate = rate

class StatsdWorker:

    def __init__(self):
        self.queue = Queue()

        # UDP connection to localhost:5189
        self.conn = statsd.StatsClient()
      
        self.p = None

    def run(self):
        if (not self.p):
            self.p = Thread(target=_worker_loop, args=(self,))
            self.p.daemon = True
            self.p.start()

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
        self.conn.gauge(state, val, rate)

    def timing(self, stat, delta, rate=1):
        self.conn.timing(stat, delta, rate)
    
    def distinct(self, stat, value):
        self.conn.set(stat, value)

# Globals

__STATSD_WORKER__ = StatsdWorker()
__STATSD_WORKER__.run()
