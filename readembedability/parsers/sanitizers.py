from glob import glob
from os import path

from readability.readability import Document
import goose

from readembedability.parsers.html import sanitize_html, SmartHTMLDocument
from readembedability.parsers.text import Summarizer
from readembedability.utils import unique, longest
from readembedability.parsers.base import BaseParser


class StandardsParser(BaseParser):
    def enrich(self, result):
        if self.bs is None:
            return result

        articles = self.bs.find_all(itemtype=["http://schema.org/Article", "http://schema.org/BlogPosting"])
        content = longest(map(str, articles))
        if content is not None:
            content = sanitize_html(content)

        parts = self.bs.find_all(itemprop='articleBody')
        if len(parts) > 0:
            content = sanitize_html("".join(map(str, parts)))

        if content is not None and len(content.strip()) > 5:
            result.set('content', content, lock=True)
            result.set('_text', SmartHTMLDocument(content).getText(), lock=True)

        keywords = result.get('keywords')
        for genre in self.bs.find_all(itemprop="genre"):
            keywords.append(genre['content'].strip())
        result.set('keywords', list(set(keywords)))

        return result


class ReadableLxmlParser(BaseParser):
    def couldBeCode(self, content):
        if content.count('=') > 5:
            return True
        return False

    def enrich(self, result):
        try:
            doc = Document(self.content, url=self.url)
            content = doc.summary(html_partial=True)
            sanitized = sanitize_html(content)
            if not self.couldBeCode(sanitized):
                result.setIfLonger('content', sanitized)
            result.setIfLonger('title', doc.short_title())
        except:
            pass
        return result


# due to https://github.com/grangier/python-goose/issues/104 - we have to create our own
# stopwords class
GOOSE_STOPWORD_LANGUAGE_PATH = path.realpath(path.join(goose.__file__, '..', 'resources', 'text', 'stopwords-*.txt'))
GOOSE_STOPWORD_LANGUAGES = [path.basename(f).split('-')[1].split('.')[0] for f in glob(GOOSE_STOPWORD_LANGUAGE_PATH)]


class GooseParserStopwords(goose.text.StopWords):
    def __init__(self, language='en'):
        if language not in GOOSE_STOPWORD_LANGUAGES:
            language = 'en'
        goose.text.StopWords.__init__(self, language)


class GooseParser(BaseParser):
    def enrich(self, result):
        g = goose.Goose({'enable_image_fetching': False, 'stopwords_class': GooseParserStopwords})
        try:
            article = g.extract(url=self.url, raw_html=self.content)
            result.setIfLonger('title', article.title)
            if len(article.cleaned_text) > 5:
                paragraphs = filter(lambda x: len(x.strip()) > 0 and 'photo b' not in x.lower(), article.cleaned_text.split("\n"))
                result.set('_text', " ".join(paragraphs))
                content = "<p>" + "</p><p>".join(paragraphs) + "</p>"
                result.setIfLonger('content', sanitize_html(content))
        except ValueError:
            pass
        return result


class LastDitchParser(BaseParser):
    """
    If we've gotten nothing so far, try something that may be stupid.
    """
    def enrich(self, result):
        if (result.get('content') is not None and len(result.get('content')) > 0) or self.bs is None:
            return result

        html = " ".join([n.string for n in self.bs.find_all("noscript") if n.string is not None])
        html = html.strip()
        if len(html) == 0:
            html = self.bs.getText().strip()

        try:
            doc = Document(html, url=self.url)
            content = doc.summary(html_partial=True)
            result.set('content', sanitize_html(content))
        except Exception:
            pass

        return result


class SummarizingParser(BaseParser):
    def enrich(self, result):
        if self.bs is None:
            return result

        if '_text' not in result:
            result.set('_text', self.bs.getText())

        s = Summarizer(result.get('_text'), result.get('title'))
        summary = s.summary()
        if len(summary) > 0:
            result.set('summary', s.summary(), lock=True)
        keywords = unique(result.get('keywords') + s.keywords())
        result.set('keywords', keywords)
        return result


class FinalContentPass(BaseParser):
    # 1) remove title from content if it's the first item
    # 2) remove all links that just contain social crap
    def enrich(self, result):
        if result.get('content') is None:
            return result

        self.cbs = SmartHTMLDocument(result.get('content'))
        result = self.remove_title(result)
        result = self.remove_social_links(result)
        return result


    def remove_social_links(self, result):
        """
        Don't do anything here.  We should actually be checking the href on the a's to
        make sure they're share links.
        """
        return result

        verboten = ['twitter', 'facebook', 'google', 'google+', 'pinterest']
        for a in self.cbs.find_all('a'):
            if self.cbs.getText(a).strip().lower().replace(' ', '') in verboten:
                a.extract()
        result.set('content', str(self.cbs), overwrite=True)
        return result


    def remove_title(self, result):
        title = result.get('title')
        if title is not None and result.get('content') is not None:
            title = title.lower().strip()
            tnodes = self.cbs.getTextNodes()
            # if first text node is title, remove it
            if len(tnodes) > 0 and unicode(tnodes[0]).lower().strip() == title:
                node = tnodes[0]
                while node.parent is not None and self.cbs.getText(node.parent).lower().strip() == title:
                    node = node.parent
                node.extract()
                result.set('content', str(self.cbs), overwrite=True)
        return result
