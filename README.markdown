# Python Distributed Hash Table
[![Build Status](https://secure.travis-ci.org/bmuller/readembedable.png?branch=master)](https://travis-ci.org/bmuller/readembedable)

## Installation

```
pip install readembedable
```

## Usage
*This assumes you have a working familiarity with [Twisted](https://twistedmatrix.com).*

Assuming you want to connect to an existing network (run the standalone server example below if you don't have a network):

```python
from twisted.internet import reactor
from twisted.python import log
from from readembedability.requests import getReadembedable
import sys

# log to std out
log.startLogging(sys.stdout)

# code here

reactor.run()
```

## Running Tests
To run tests:

```
trial readembedable
```
