from urlparse import urlparse, parse_qs, urlunparse
from urllib import urlencode
import re
import operator
import datetime
from collections import Counter

from twisted.internet import defer

URL_DATE_MDY = re.compile("/\d\d?/\d\d?/\d\d\d\d/")
URL_DATE_YMD = re.compile("/\d\d\d\d/\d\d?/\d\d?/")


class URL:
    def __init__(self, url):
        if isinstance(url, unicode):
            url = url.encode('ascii', errors='ignore')
        self._parts = list(urlparse(url))
        self._query = parse_qs(self._parts[4])

    def getPath(self):
        return self._parts[2]

    def getHost(self):
        return self._parts[1]

    def getParam(self, name, default=None):
        return self._query.get(name, [default])[0]

    def setParam(self, name, value):
        self._query[name] = [value]
        return self

    def getDate(self):
        url = self._parts[2]
        year, month, day = None, None, None
        match = URL_DATE_YMD.search(url)
        if match is not None:
            year, month, day = match.group(0)[1:-1].split('/')
        else:
            match = URL_DATE_MDY.search(url)
            if match is not None:
                month, day, year = match.group(0)[1:-1].split('/')

        if month is not None and day is not None:
            if int(month) > 12:
                month, day = day, month
            return datetime.datetime(*map(int, [year, month, day]))

        return None

    def __str__(self):
        nquery = {}
        for key, values in self._query.iteritems():
            nquery[key] = values[0]
        self._parts[4] = urlencode(nquery)
        return urlunparse(self._parts)

    def startswith(self, prefix):
        return str(self).lower().startswith(prefix.lower())


def unique(iterable):
    """
    In order uniquer - (cause list(set(iter)) doesn't maintain order)
    """
    result = []
    for x in iterable:
        if x not in result:
            result.append(x)
    return result


def longest(iterable):
    if len(iterable) == 0:
        return None

    longest = iterable[0]
    for item in iterable[1:]:
        if len(item) > len(longest):
            longest = item
    return longest


def most_common(iterable, count=1):
    common = Counter(iterable).most_common(count)
    return map(operator.itemgetter(0), common)


def deferredDict(d):
    """
    Just like a C{defer.DeferredList} but instead accepts and returns a C{dict}.

    @param d: A C{dict} whose values are all C{Deferred} objects.

    @return: A C{DeferredList} whose callback will be given a dictionary whose
    keys are the same as the parameter C{d}'s and whose values are the results
    of each individual deferred call.
    """
    if len(d) == 0:
        return defer.succeed({})

    def handle(results, names):
        rvalue = {}
        for index in range(len(results)):
            rvalue[names[index]] = results[index][1]
        return rvalue

    dl = defer.DeferredList(d.values())
    return dl.addCallback(handle, d.keys())
