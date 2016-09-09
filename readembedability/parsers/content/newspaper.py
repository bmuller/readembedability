import re

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
        # html = cls.get_unicode_html(html)
        if html.startswith('<?'):
            html = re.sub(r'^\<\?.*?\?\>', '', html, flags=re.DOTALL)

        # lxml parser must have utf8, though the next line was causing
        # issues when the html was already utf8
        # html = codecs.encode(html, 'utf-8')
        cls.doc = lxml.html.fromstring(html)
        return cls.doc


class FixedArticleConfig(ArticleConfiguration):
    def get_parser(self):
        return FixedParser


class NewspaperParser(BaseParser):
    async def enrich(self, result):
        article = Article(self.url, config=FixedArticleConfig())
        article.config.fetch_images = False
        article.set_html(sanitize_html(self.response.body))
        article.parse()

        result.set_if_longer('title', article.title, 2)
        if len(article.meta_description) > 0:
            result.set_if_longer('subtitle', article.meta_description, 2)

        if len(article.article_html) > 0:
            sanitized = sanitize_html(article.article_html)
            result.set_if_longer('content', sanitized)
        elif article.top_node is not None:
            sanitized = sanitize_html(tostring(article.top_node))
            result.set('content', sanitized, 2)

        if article.authors:
            result.set('authors', article.authors, 2)
        if article.publish_date and len(str(article.publish_date)) > 0:
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

        if len(text) > 0:
            result.set('_text', text, 2)

        return result
