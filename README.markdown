# Readembedability
[![Build Status](https://secure.travis-ci.org/bmuller/readembedability.png?branch=master)](https://travis-ci.org/bmuller/readembedability)

## Installation
Readembedability is an open source version of [Readability](https://readability.com/) or [Diffbot](https://www.diffbot.com/) that also handles creating a unified view of [oEmbed](http://www.oembed.com/) pages (for instance, twitter or youtube pages).

```
pip install readembedability
```

## Usage
Assume you want to extract all of the meaningful data from an article on the NY Times:

```python
from readembedability.page import get_readembedable
import asyncio

loop = asyncio.get_event_loop()
url = "www.nytimes.com/politics/first-draft/2015/03/13/judge-orders-state-dept-to-release-records-from-clinton-trips/"
result = loop.run_until_complete(get_readembedable(url))
print(result)
```

The result of calling `get_readembedable` will give you a dictionary with the following keys:
 * primary_image: The full URL to the image that is most likely the primary one for the page.
 * secondary_images: A list of all other images that appear and seem related to the content.
 * authors: The author names, if it can be pulled out.
 * url: The original URL passed as a parameter.
 * canonical_url: The URL for the page that had the content (for instance, after following all redirects) 
 * title: Page title
 * summary: Few sentence summary of the content
 * content: Meaningful/relevant text content from the page.
 * published_at: Date of publishing.
 * keywords: Keywords pulled from the content
 * embed: Whether the content is HTML suitable for embedding (for instance, via oEmbed)

## How It Works
Readembedability utilizes a number of libraries that all try to extract meaningful information from poorly structured web pages.  It runs content through all of them, extracting the best guess at, say, the author after each pass.  Some libraries are good at extracting text, others at images, etc.  Readembedability uses each library for the task it seems best able to perform.

## Running Tests
To run tests:

```
python -m unittest
```
