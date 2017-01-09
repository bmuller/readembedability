import re
from operator import itemgetter

from readembedability.io import get_page
from readembedability.utils import parse_date
from readembedability.parsers.base import BaseParser
from readembedability.parsers.html import SmartHTMLDocument


class CustomParser(BaseParser):
    PARSERS = []

    @classmethod
    def register(cls, regex, fclass):
        # pylint: disable=no-member
        regex = re.compile(regex, re.IGNORECASE)
        cls.PARSERS.append((regex, fclass))

    async def enrich(self, result):
        for regex, fclass in CustomParser.PARSERS:
            if regex.match(self.response.url) is not None:
                return await fclass(self.response).enrich(result)
        return result


class NYTimesParser(CustomParser):
    async def enrich(self, result):
        loginurl = 'https://myaccount.nytimes.com/auth/login'
        if self.response.url.startswith(loginurl):
            result.set('success', False, 4)
        return result


# pylint: disable=anomalous-backslash-in-string
CustomParser.register("https?://.*\.nytimes\.com/", NYTimesParser)
