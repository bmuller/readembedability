from operator import methodcaller
from datetime import datetime

from readembedability.parsers.html import sanitize_html, SmartHTMLDocument
from readembedability.utils import unique, longest, parse_date, URL
from readembedability.parsers.base import BaseParser


class AuthorParser(BaseParser):
    # pylint: disable=no-self-use
    def fix_name(self, author):
        author = author.strip()
        # if all upcase, then just capitalize
        if author == author.upper():
            parts = map(methodcaller('capitalize'), author.split(' '))
            author = " ".join(parts)
        return author

    # pylint: disable=no-self-use
    def has_byline_prefix(self, prefix):
        prefix = prefix.lower()
        for allowed in ['by']:
            hasp = prefix.startswith(allowed)
            if hasp and len(prefix) == len(allowed):
                return True
            if hasp and not prefix[len(allowed)].isalpha():
                return True
        return False

    def get_standards(self):
        attempts = [
            ('meta', 'content', {'name': 'author'}),
            (None, None, {'itemprop': 'author'}),
            ('a', None, {'rel': 'author'})
        ]
        return self.soup.coalesce_elem_value(attempts)

    async def enrich(self, result):
        if self.soup is None:
            return result

        # try standards based approach
        author = self.get_standards()
        if author is not None:
            result.set('authors', [self.fix_name(author)], 3)
            return result

        for txt in self.soup.text_chunks():
            parts = [s for s in txt.split(' ') if s != ""]
            if len(parts) == 0:
                return result
            # overlen is the max length + 1 for an author string
            overlen = 8 + (txt.lower().count(' and ') * 8)
            overlen += (txt.count(',') * 8)
            isbyline = self.has_byline_prefix(parts[0])
            if len(parts) in range(2, overlen) and isbyline:
                name = " ".join(parts[1:])
                if author is None or len(name) < author:
                    author = name

        if author:
            authors = map(self.fix_name, author.split(' and '))
            result.set('authors', list(authors))
        return result


class DatePublishedParser(BaseParser):
    def get_standards(self):
        attempts = [
            (None, None, {'itemprop': 'datePublished'}),
            ('meta', 'content', {'itemprop': 'datePublished'}),
            ('meta', 'content', {'name': 'PublishDate'}),
            ('meta', 'content', {'name': 'CreationDate'}),
            ('time'),
            ('meta', 'content', {'name': 'eomportal-lastUpdate'})
        ]
        return self.soup.coalesce_elem_value(attempts)

    async def enrich(self, result):
        if self.soup is None:
            result.set('published_at', None)
            return result

        pat = self.get_standards()
        if pat is not None:
            pat = parse_date(pat)

        # last ditch, check url
        if pat is None:
            pat = URL(self.url).url_date

        # Don't set any published_at to be in the future
        if pat is not None and pat < datetime.now().replace(tzinfo=pat.tzinfo):
            result.set('published_at', pat)
        return result


class StandardsParser(BaseParser):
    async def enrich(self, result):
        if self.soup is None:
            return result

        atypes = ["http://schema.org/Article", "http://schema.org/BlogPosting"]
        articles = self.soup.find_all(itemtype=atypes)
        content = longest(map(str, articles))
        if content is not None:
            content = sanitize_html(content)

        parts = self.soup.find_all(itemprop='articleBody')
        if len(parts) > 0:
            content = sanitize_html("".join(map(str, parts)))

        if content is not None and len(content.strip()) > 5:
            result.set('content', content, 3)
            result.set('_text', SmartHTMLDocument(content).all_text(), 3)

        keywords = result.get('keywords')
        for genre in self.soup.find_all(itemprop="genre", content=True):
            keywords.append(genre['content'].strip())
        result.set('keywords', unique(keywords))

        return result


class SocialParser(BaseParser):
    async def enrich(self, result):
        if not self.soup:
            return result

        ogtitle = self.soup.find_all("meta", property="og:title", content=True)
        if ogtitle:
            result.set('title', ogtitle[0]['content'], 2)

        attrs = {'property': 'og:description', 'content': True}
        ogdesc = self.soup.find_all("meta", **attrs)
        if ogdesc:
            result.set_if_longer('summary', ogdesc[0]['content'])
        return result
