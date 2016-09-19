import unittest

from readembedability.parsers.meta import AuthorParser
from readembedability.parsers.result import ParseResult
from readembedability.tests.utils import FakeResponse, async_test
from readembedability.tests.soupkitchen import T


class AuthorParserTest(unittest.TestCase):
    @async_test
    async def test_extract_byline(self):
        link = T.a("by ", T.span("SNAKE PLISSKEN"), href='#')
        html = T.html(T.body(T.p("some content"), link))
        aparser = AuthorParser(FakeResponse(str(html)))
        result = await aparser.enrich(ParseResult(""))
        self.assertEqual(result.get('authors'), ["Snake Plissken"])
