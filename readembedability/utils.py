from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import re
import datetime
from collections import Counter

from dateutil.parser import parse as dateutil_parse

# pylint: disable=anomalous-backslash-in-string
URL_DATE_MDY = re.compile("/\d\d?/\d\d?/\d\d\d\d/")
URL_DATE_YMD = re.compile("/\d\d\d\d/\d\d?/\d\d?/")


class URL:
    def __init__(self, url):
        if not url.startswith('http'):
            url = 'http://' + url
        self._parts = list(urlparse(url))
        self._query = parse_qs(self._parts[4])

    @property
    def basename(self):
        return self.path.split('/')[-1]

    @property
    def path(self):
        return self._parts[2]

    @property
    def host(self):
        return self._parts[1]

    @property
    def top_host(self):
        parts = self.host.split('.')
        if len(parts) < 2:
            return parts[0]
        return ".".join(parts[-2:])

    @property
    def url_date(self):
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

    def get_param(self, name, default=None):
        return self._query.get(name, [default])[0]

    def set_param(self, name, value):
        self._query[name] = [value]
        return self

    def set_params(self, **kwargs):
        for key, value in kwargs.items():
            self.set_param(key, value)
        return self

    def startswith(self, prefix):
        return str(self).lower().startswith(prefix.lower())

    def __str__(self):
        nquery = {}
        for key, values in self._query.items():
            nquery[key] = values[0]
        self._parts[4] = urlencode(nquery)
        return urlunparse(self._parts)


def unique(iterable):
    """
    In order uniquer - (cause list(set(iter)) doesn't maintain order).
    Should be the fastest way to do this per:
    https://www.peterbe.com/plog/uniqifiers-benchmark
    """
    result = []
    seen = {}
    for item in iterable:
        if item not in seen:
            seen[item] = 1
            result.append(item)
    return result


def longest(iterable):
    best = None
    for item in iterable:
        if best is None or len(item) > len(best):
            best = item
    return best


def most_common(iterable, count=1):
    common = Counter(iterable).most_common(count)
    return [i[0] for i in common]


def parse_date(datestring):
    try:
        return dateutil_parse(datestring, fuzzy=True)
    except (ValueError, OverflowError):
        return None
