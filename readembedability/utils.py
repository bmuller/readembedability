from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import re
import operator
import datetime
from collections import Counter

URL_DATE_MDY = re.compile("/\d\d?/\d\d?/\d\d\d\d/")
URL_DATE_YMD = re.compile("/\d\d\d\d/\d\d?/\d\d?/")


class URL:
    def __init__(self, url):
        if not url.startswith('http'):
            url = 'http://' + url
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

    def setParams(self, **kwargs):
        for k, v in kwargs.iteritems():
            self.setParam(k, v)
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
        for key, values in self._query.items():
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
    longest = None
    for item in iterable:
        if longest is None or len(item) > len(longest):
            longest = item
    return longest


def most_common(iterable, count=1):
    common = Counter(iterable).most_common(count)
    return [i[0] for i in common]
