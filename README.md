# pystatsd

Thread Safe Statsd Python API

## Requirements
 
 * Python 2.7 or newer
 * statsd 3.2.1 or newer
 * enum34 1.1.2 or newer

## Building

    make

## Usage

```python
import pystatsd

# Increment a counter named foo.counter by 1
pystatsd.increment("foo.counter", 1)

# Decrement the same counter by 10
pystatsd.increment("foo.counter", 10)

# Set the value of a gauge to 450
pystatsd.set("foo.gauge", 450)

# Increment and decrement the same gauge as before
pystatsd.increment("foo.gauge", 100, gauge=True)
pystatsd.decrement("foo.gauge", 10, gauge=True)

# Measure a timing value
pystatsd.timing("foo.timing", 300)
```

## Running Tests

    make check
