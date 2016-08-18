from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag, Comment, ProcessingInstruction
from bs4.element import Declaration, CData, Doctype

from tidylib import tidy_fragment

CLEAN_ELEMS = [
    "article",
    "object",
    "iframe",
    "img",
    "ul",
    "li",
    "ol",
    "p",
    "span",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "i",
    "b",
    "code",
    "pre",
    "em",
    "blockquote",
    "table",
    "thead",
    "tbody",
    "td",
    "tr",
    "dt",
    "dl",
    "caption",
    "col",
    "colgroup",
    "tfoo",
    "video"
]

CLEAN_ELEM_ATTRS = {
    'a': ['href'],
    'img': ['src'],
    'iframe': ['*'],
    'video': ['*']
}


def sanitize_html(html):
    soup = BeautifulSoup(html, 'lxml')
    if soup.html.body is None:
        return ""

    for elem in list(soup.html.body.descendants):
        smart = SmartElem(elem)
        if not smart.is_virtuous():
            smart.delete()
        else:
            smart.clean()

    html = "".join([str(c) for c in soup.html.body.children])
    doc, _ = tidy_fragment(html, options={'indent': 0})
    return doc


class SmartElem:
    def __init__(self, elem):
        self.elem = elem

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
        if self.elem.name not in CLEAN_ELEMS:
            return False
        if self.elem.name == 'a' and 'sign up' in self.elem.get_text().lower():
            return False
        # the class attribute is a list
        if 'caption' in " ".join(self.elem.attrs.get('class', [])):
            return False
        return True

    def _is_virtuous_text(self):
        text = str(self.elem).lower()
        return not text.startswith('photo by') and len(text) > 0

    def is_virtuous(self):
        """
        Is this node useful?  Does it likely contain good information?
        """
        if self.is_tag() and self._is_virtuous_tag():
            return True
        elif self.is_text() and self._is_virtuous_text():
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

    def type_guess(self):
        guess = None
        ogtype = self.find_all("meta", property="og:type", content=True)
        if len(ogtype) > 0:
            guess = ogtype[0]['content']
        return guess

    @property
    def body(self):
        return self.soup.html.body

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
            elif elem[attr] is not None and len(elem[attr].strip()) > 0:
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
            if result is not None:
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
