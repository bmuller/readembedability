# Python Distributed Hash Table
[![Build Status](https://secure.travis-ci.org/bmuller/readembedability.png?branch=master)](https://travis-ci.org/bmuller/readembedability)

## Installation
Readembedability is an open source version of [Readability](https://readability.com/) or [Diffbot](https://www.diffbot.com/) that also handles creating a unified view of [oEmbed](http://www.oembed.com/) pages (for instance, twitter or youtube pages).

```
pip install readembedable
```

## Usage
*This assumes you have a working familiarity with [Twisted](https://twistedmatrix.com).*

Assuming you want to connect to an existing network (run the standalone server example below if you don't have a network):

```python
from twisted.internet import reactor
from twisted.python import log
from readembedability.page import getReadembedable
import sys

# log to std out
log.startLogging(sys.stdout)

def p(r):
    print r
    reactor.stop()

url = "www.nytimes.com/politics/first-draft/2015/03/13/judge-orders-state-dept-to-release-records-from-clinton-trips/"
getReadembedable(url).addCallback(p)
reactor.run()
```

The result of calling `getReadembedable` will give you a dictionary with the following keys:
 * primary_image: The full URL to the image that is most likely the primary one for the page.
 * secondary_images: A list of all other images that appear and seem related to the content.
 * author: The author name, if it can be pulled out.
 * url: The original URL passed as a parameter.
 * canonical_url: The URL for the page that had the content (for instance, after following all redirects) 
 * title: Page title
 * summary: Few sentence summary of the content
 * content: Meaningful/relevant text content from the page.
 * published_at: Date of publishing.
 * keywords: Keywords pulled from the content
 * embed: Whether the content is HTML suitable for embedding (for instance, via oEmbed)

## Running Tests
To run tests:

```
trial readembedable
```
