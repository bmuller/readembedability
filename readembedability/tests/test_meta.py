from twisted.trial import unittest

from readembedability.parsers.meta import AuthorParser
from readembedability.parsers.base import ParseResult
from readembedability.tests.utils import FakeResponse
from readembedability.tests.soupkitchen import T


class AuthorParserTest(unittest.TestCase):

    def test_fixName(self):
        ap = AuthorParser(FakeResponse(""))
        self.assertEqual(ap.fixName("SNAKE PLISSKEN"), "Snake Plissken")
        self.assertEqual(ap.fixName(None), None)

    def test_extractByline(self):
        html = T.html(T.body(T.p("some content"), T.a("by ", T.span("SNAKE PLISSKEN"), href='#')))
        ap = AuthorParser(FakeResponse(str(html)))
        result = ap.enrich(ParseResult())
        self.assertEqual(result.get('author'), "Snake Plissken")
