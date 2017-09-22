# pystatsd

Thread Safe Statsd Python API

## Requirements
 
 * Python 2.7 or newer

## Building

```bash
    make
```

## Installing

```bash
    make install
```

## Usage

```python
import pystatsd

# Increment a counter named foo.counter by 1
pystatsd.increment("foo.counter")

# Decrement the same counter by 10
pystatsd.decrement("foo.counter", 10)

# Decrement the same counter by 1 with a sample rate of 0.5
pystatsd.decrement("foo.counter", rate=0.5)

# Set the value of a gauge to 450
pystatsd.set("foo.gauge", 450)

# Increment a gauge by 1
pystatsd.increment("foo.gauge", gauge=True)

# Decrement a gauge by 10
pystatsd.decrement("foo.gauge", 10, gauge=True)

# Measure a timing value
pystatsd.timing("foo.timing", 300)

# Measure a timing value with a context manager
with pystatsd.Timer("foo.timing.context.manager"):
    for i in range(1, 1000):
        pass

# Measure a timing value with a decorator
@pystatsd.Timer('foo.timing.decorator')
def foo():
    for i in range(1, 1000):
        pass
```

## Running Tests

### Prerequisites

* tox

```bash
    make check
```
