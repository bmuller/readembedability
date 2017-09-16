import re
import codecs

import lxml.html
# pylint: disable=no-name-in-module
from lxml.etree import tostring
from newspaper import Article
from newspaper.configuration import ArticleConfiguration
from newspaper.parsers import Parser

from readembedability.parsers.base import BaseParser
from readembedability.parsers.text import Summarizer
from readembedability.parsers.html import sanitize_html


class FixedParser(Parser):
    """
    This exists because the original:
    https://github.com/codelucas/newspaper/blob/master/newspaper/parsers.py

    swallows the exception.
    """
    @classmethod
    def fromstring(cls, html):
        # next line shouldn't be necessary because
        # we will always sanitize_html before passing in
        # which will always result in unicode
        # html = cls.get_unicode_html(html)
        # pylint: disable=no-member
        if html.startswith('<?'):
            html = re.sub(r'^\<\?.*?\?\>', '', html, flags=re.DOTALL)

        # lxml parser must have utf8.  We have unicode, though not
        # necessarily utf8 - so if there's an issue with 'switching
        # encoding' then we force utf8 encoding and try again
        try:
            cls.doc = lxml.html.fromstring(html)
        # pylint: disable=no-member
        except lxml.etree.XMLSyntaxError as error:
            if 'switching encoding' not in str(error):
                raise error
            html = codecs.encode(html, 'utf-8')
            cls.doc = lxml.html.fromstring(html)
        return cls.doc


class FixedArticleConfig(ArticleConfiguration):
    def get_parser(self):
        return FixedParser


class NewspaperParser(BaseParser):
    async def enrich(self, result):
        # none of the following lines will work if we couldn't make soup
        if not self.soup:
            return result

        sanitized = sanitize_html(self.response.body)
        if not sanitized:
            return result

        article = Article(self.url, config=FixedArticleConfig())
        article.config.fetch_images = False
        article.set_html(sanitized)
        article.parse()

        result.set_if('title', article.title.strip(), confidence=2, tiebreaker='textlength')
        if article.meta_description:
            result.set('subtitle', article.meta_description, 2, 'textlength')

        if article.article_html:
            sanitized = sanitize_html(article.article_html)
            result.set('content', sanitized, 0, 'textlength')
        elif article.top_node is not None:
            sanitized = sanitize_html(tostring(article.top_node))
            result.set('content', sanitized, 2)

        if article.authors:
            result.set('authors', article.authors, 2)
        if article.publish_date and str(article.publish_date):
            result.set('published_at', article.publish_date, 2)
        result.add('keywords', list(article.keywords))
        result.add('keywords', list(article.tags))
        result.add('_candidate_images', list(article.imgs))
        # Primary image guess is actually pretty crappy
        if article.top_image:
            result.add('_candidate_images', [article.top_img])

        text = ""
        for paragraph in article.text.split("\n"):
            paragraph = paragraph.strip()
            # this is done to get rid of cases where a stray heading
            # like "Photographs" ends up as a paragraph
            if Summarizer.has_sentence(paragraph):
                text += " " + paragraph

        if text:
            result.set('_text', text, 2)

        return result
