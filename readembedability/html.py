from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag, Comment

from tidylib import tidy_fragment

CLEAN_ELEMS = ("article object iframe img ul li ol p span div h1 h2 h3 h4 h5 h6 a i b code " +
               "pre em blockquote table thead tbody td tr dt dl caption col colgroup tfoo video").split()

CLEAN_ELEM_ATTRS = { 'a': ['href'], 'img': ['src'], 'iframe': ['*'], 'video': ['*'] }


def sanitize_html(html):
    return Sanitizer(html).clean()


class Sanitizer:
    def __init__(self, html):
        self.bs = BeautifulSoup(html)

    @property
    def body(self):
        return self.bs.html.body

    def _cleanAttrs(self, elem):
        attrs = {}
        for name, value in elem.attrs.items():
            if name in CLEAN_ELEM_ATTRS.get(elem.name, []):
                attrs[name] = value
        elem.attrs = attrs

    def _isBad(self, elem):
        if elem.name == 'a' and 'sign up' in elem.get_text().lower():
            return True
        return False

    def _tag(self, elem):
        if elem.name not in CLEAN_ELEMS or self._isBad(elem):
            elem.extract()
        else:
            self._cleanAttrs(elem)

    def clean(self):
        if self.bs.html.body is None:
            return ""
        for elem in list(self.bs.html.body.descendants):
            # only allow tags and strings
            if type(elem) is Tag:
                self._tag(elem)
            elif type(elem) is Comment or type(elem) is not NavigableString or 'photo by' in elem.string.lower():
                elem.extract()

        html = "".join([str(c) for c in self.bs.html.body.children])
        html = html.decode('utf-8')
        doc, errors = tidy_fragment(html, options={'indent': 0})
        return doc


class SmartHTMLDocument:
    def __init__(self, html):
        self.bs = BeautifulSoup(html)
        # cache chunks
        self.chunks = None

    @property
    def body(self):
        return self.bs.html.body

    def find_all(self, *args, **kwargs):
        return self.bs.find_all(*args, attrs=kwargs)


    def delete(self, *args, **kwargs):
        for elem in self.bs.find_all(*args, attrs=kwargs):
            elem.extract()


    def getElementValue(self, _name, attr=None, **attrs):
        for elem in self.find_all(_name, **attrs):
            if attr is None:
                txt = elem.get_text().strip()
                if txt != "":
                    return txt
            elif elem[attr] is not None and len(elem[attr].strip()) > 0:
                return elem[attr].strip()
        return None


    def getText(self, node=None):
        text = ""
        node = node or self.bs.html
        if type(node) is not Tag:
            return text
        for child in node.descendants:
            if self.isTextNode(child):
                text += " " + child.string
        return text


    def getTextNodes(self):
        """
        Return all non-empty, non-js, non-css, non-comment text nodes
        """
        if self.bs.html is None:
            return []
        return [c for c in self.bs.html.descendants if self.isTextNode(c) and len(unicode(c).strip()) > 0]


    def isTextNode(self, node):
        istnode = type(node) is NavigableString
        istnode = istnode and (node.parent is None or node.parent.name not in [ 'script', 'style' ])
        return istnode and type(node) is not Comment


    def textChunks(self):
        if self.chunks is not None:
            return self.chunks

        self.chunks = []
        for child in self.bs.html.descendants:
            txt = self.getText(child).strip()
            if txt != "":
                self.chunks.append(txt)
        return self.chunks


    def __str__(self):
        if self.bs.html is None or self.bs.html.body is None:
            return ""
        return "".join([str(c) for c in self.bs.html.body.children])
