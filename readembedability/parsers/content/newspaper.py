import re

import lxml.html
from newspaper import Article
from newspaper.configuration import ArticleConfiguration
from newspaper.parsers import Parser

from readembedability.parsers.base import BaseParser
from readembedability.parsers.text import Summarizer
from readembedability.parsers.html import sanitize_html


class FixedParser(Parser):
    @classmethod
    def fromstring(cls, html):
        if html.startswith('<?'):
            html = re.sub(r'^\<\?.*?\?\>', '', html, flags=re.DOTALL)
        cls.doc = lxml.html.fromstring(html.encode('utf-8'))
        return cls.doc


class FixedArticleConfig(ArticleConfiguration):
    def get_parser(self):
        return FixedParser


class NewspaperParser(BaseParser):
    async def enrich(self, result):
        article = Article(self.url, config=FixedArticleConfig())
        article.config.fetch_image = False
        article.set_html(sanitize_html(self.response.body))
        article.parse()

        result.set_if_longer('title', article.title, 2)
        if len(article.meta_description) > 0:
            result.set_if_longer('subtitle', article.meta_description, 2)
        if len(article.article_html) > 0:
            sanitized = sanitize_html(article.article_html)
            result.set_if_longer('content', sanitized)
        if article.authors:
            result.set('authors', article.authors, 2)
        if len(str(article.publish_date)) > 0:
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
                text += paragraph

        if len(text) > 0:
            result.set('_text', text, 2)

        return result
