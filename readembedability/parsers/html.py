import re

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag, Comment, ProcessingInstruction
from bs4.element import Declaration, CData, Doctype

import tidylib

CLEAN_ELEMS = [
    "a",
    "article",
    "b",
    "blockquote",
    "caption",
    "code",
    "col",
    "colgroup",
    "dt",
    "dl",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "i",
    "iframe",
    "img",
    "li",
    "main",
    "object",
    "ol",
    "p",
    "pre",
    "section",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "tfoo",
    "thead",
    "tr",
    "ul",
    "video"
]

CLEAN_ELEM_ATTRS = {
    'a': ['href'],
    'img': ['src'],
    'iframe': ['*'],
    'video': ['*']
}


def tidy_html(html):
    doc, _ = tidylib.tidy_fragment(html, options={'indent': 0})
    return doc


def sanitize_html(html):
    # remove unknown silly elements, like <cnt> in
    # washingtonexaminer articles
    html = tidy_html(html)
    soup = BeautifulSoup(html, 'lxml')
    if not soup.html or not soup.html.body:
        return ""

    for elem in list(soup.html.body.descendants):
        smart = SmartElem(elem)
        if not smart.is_virtuous():
            smart.delete()
        else:
            smart.clean()

    html = "".join([str(c) for c in soup.html.body.children])
    return tidy_html(html)


class SmartElem:
    def __init__(self, elem):
        self.elem = elem
        self.attrs = self.elem.attrs if hasattr(self.elem, 'attrs') else {}

    def is_text(self):
        if not isinstance(self.elem, NavigableString):
            return False

        for badtype in [Comment, ProcessingInstruction, Declaration,
                        CData, Doctype]:
            if isinstance(self.elem, badtype):
                return False

        badparents = ['script', 'style']
        return self.elem.parent and self.elem.parent.name not in badparents

    def is_tag(self):
        return isinstance(self.elem, Tag)

    def delete(self):
        self.elem.extract()

    def _is_virtuous_tag(self):
        result = True
        if self.elem.name not in CLEAN_ELEMS:
            result = False
        if self.elem.name == 'a':
            result = self._is_virtuous_anchor()
        if self.elem.name == 'img':
            result = self._is_virtuous_image()

        # the class attribute is a list
        cstring = " ".join(self.attrs.get('class', []))
        verbotten = ['caption', 'newsletter', 'signup']
        if any([(verb in cstring) for verb in verbotten]):
            result = False
        return result

    def _is_virtuous_image(self):
        """
        Given that this is an image, is it virtuous?
        """
        src = self.attrs.get('src')
        verbotten = ['data:image']
        if not src or any([v in src for v in verbotten]):
            return False
        return True

    def _is_virtuous_anchor(self):
        """
        Given that this is an anchor ('a' elem), is it virtuous?
        """
        text = self.elem.get_text().lower().strip()
        href = self.attrs.get('href')
        virttext = self._is_virtuous_text(text)
        if not href or href.strip() == '#' or not virttext:
            return False

        verbotten = ['sign up']
        if not text or any([v in text for v in verbotten]):
            return False

        verbotten = ['mailto:', 'javascript:', 'twitter.com/share',
                     'facebook.com/sharer/sharer.php']
        if any([v in href for v in verbotten]):
            return False
        return True

    # pylint: disable=no-self-use
    def _is_virtuous_text(self, text):
        text = text.lower()
        verbotten = [
            'advertisement',
            'photo by',
            'continue reading',
            'read more',
            'subscribe'
        ]
        for verb in verbotten:
            if text.startswith(verb):
                return False
        return len(text) > 0

    def is_virtuous(self):
        """
        Is this node useful?  Does it likely contain good information?
        """
        if self.is_tag() and self._is_virtuous_tag():
            return True
        elif self.is_text() and self._is_virtuous_text(str(self.elem)):
            return True
        return False

    def clean(self):
        if self.is_tag():
            attrs = {}
            for name, value in self.elem.attrs.items():
                if name in CLEAN_ELEM_ATTRS.get(self.elem.name, []):
                    attrs[name] = value
            self.elem.attrs = attrs
        return self.elem

    def all_text(self):
        text = ""
        if self.is_text():
            return str(self)
        elif not self.is_tag():
            # this would be a Comment, etc
            return text
        for child in self.elem.descendants:
            celem = SmartElem(child)
            if celem.is_text():
                text += " " + str(celem)
        return text.strip()

    def __str__(self):
        return str(self.elem)


class SmartHTMLDocument:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, 'lxml')

    @property
    def body(self):
        return self.soup.html.body

    @property
    def title(self):
        return self.soup.html.title

    def find_all_loose(self, *args, **kwargs):
        """
        Make all string kwarg values regexes.  This is useful in cases where
        you want itemprop='articleBody text' to be matched by 'articleBody'

        Note that re.compile does cache, but only up to re._MAXCACHE regexes
        """
        # pylint: disable=not-an-iterable
        loosekw = {}
        for key, value in kwargs.items():
            value = re.compile(value) if isinstance(value, str) else value
            loosekw[key] = value
        return self.find_all(*args, **loosekw)

    def find_all(self, *args, **kwargs):
        return self.soup.find_all(*args, attrs=kwargs)

    def delete(self, *args, **kwargs):
        for elem in self.soup.find_all(*args, attrs=kwargs):
            elem.extract()

    def get_elem_value(self, _name, attr=None, **attrs):
        for elem in self.find_all(_name, **attrs):
            if attr is None:
                txt = elem.get_text().strip()
                if txt != "":
                    return txt
            elif elem.has_attr(attr) and elem[attr].strip():
                return elem[attr].strip()
        return None

    def coalesce_elem_value(self, attempts):
        """
        Given lots of get_elem_value calls you'd like to make but
        you only care about the first non-null result, just call this
        function with tuples of your args to get_elem_value.
        """
        for attempt in map(list, attempts):
            kwargs = {}
            if len(attempt) == 3:
                kwargs = attempt.pop()
            if len(attempt) == 2:
                kwargs['attr'] = attempt.pop()
            result = self.get_elem_value(attempt[0], **kwargs)
            if result:
                return result
        return None

    def all_text(self):
        return SmartElem(self.soup.html).all_text()

    def get_text_nodes(self):
        """
        Return all non-empty, non-js, non-css, non-comment
        text nodes
        """
        result = []
        if self.soup.html is None:
            return result

        for kid in self.soup.html.descendants:
            elem = SmartElem(kid)
            if elem.is_text() and elem.is_virtuous():
                result.append(kid)
        return result

    def text_chunks(self):
        """
        Return recursive chunks of text.  For instance:
        <p>one <b>two</b></p> will return:
        ['one two', 'two']
        """
        chunks = []
        for child in self.soup.html.descendants:
            txt = SmartElem(child).all_text()
            if txt != "":
                chunks.append(txt)
        return chunks

    def __str__(self):
        if self.soup.html is None or self.soup.html.body is None:
            return ""
        return "".join([str(c) for c in self.soup.html.body.children])
