from operator import methodcaller

from datetime import datetime

from readembedability.parsers.base import BaseParser
from readembedability.utils import URL


class AuthorParser(BaseParser):
    def fixName(self, author):
        if author is None:
            return author
        author = author.strip()
        # if all upcase, then just capitalize
        if author == author.upper():
            parts = map(methodcaller('capitalize'), author.split(' '))
            author = " ".join(parts)
        return author

    def isBylinePrefix(self, prefix):
        prefix = prefix.lower()
        for allowed in ['by']:
            r = prefix.startswith(allowed)
            if r and len(prefix) == len(allowed):
                return True
            if r and not prefix[len(allowed)].isalpha():
                return True
        return False

    def enrich(self, result):
        if self.bs is None:
            result.set('author', None)
            return result

        author = self.bs.getElementValue('meta', 'content', name='author')
        author = author or self.bs.getElementValue(None, None, itemprop='author')
        author = author or self.bs.getElementValue('a', None, rel='author')
        if author is not None:
            result.set('author', self.fixName(author), lock=True)
            return result

        for astring in self.bs.textChunks():
            txt = astring.strip()
            parts = filter(lambda s: s != "", txt.split(' '))
            allowedlen = 4 + (txt.lower().count(' and ') * 4) + (txt.count(',') * 4)
            if len(parts) > 1 and len(parts) <= allowedlen and self.isBylinePrefix(parts[0]):
                name = " ".join(parts[1:])
                if author is None or len(name) < author:
                    author = name

        result.set('author', self.fixName(author))
        return result


class DatePublishedParser(BaseParser):
    def enrich(self, result):
        if self.bs is None:
            result.set('published_at', None)
            return result

        pat = self.bs.getElementValue(None, None, itemprop='datePublished')
        pat = pat or self.bs.getElementValue('meta', 'content', itemprop='datePublished')
        pat = pat or self.bs.getElementValue('meta', 'content', name='PublishDate')
        pat = pat or self.bs.getElementValue('meta', 'content', name='CreationDate')
        pat = pat or self.bs.getElementValue('time')
        # this is unique to methode
        pat = pat or self.bs.getElementValue('meta', 'content', name='eomportal-lastUpdate')

        if pat is not None:
            pat = self.parse_date(pat)

        # last ditch, check url
        if pat is None:
            pat = URL(self.url).getDate()

        # Don't set any published_at to be in the future
        if pat is not None and pat < datetime.now().replace(tzinfo=pat.tzinfo):
            result.set('published_at', pat)
        return result
