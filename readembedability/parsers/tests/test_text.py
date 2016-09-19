import unittest

from readembedability.parsers.text import parse_authors, fix_name


class TextTest(unittest.TestCase):
    def test_fix_name(self):
        self.assertEqual(fix_name("BILL BRADLEY"), "Bill Bradley")
        self.assertEqual(fix_name("Bill McClintock"), "Bill McClintock")

    def test_parse_authors(self):
        comparisons = [
            ("BY: BILL BRADLEY", ["Bill Bradley"]),
            ("BY: BILL BRADLEY AND Sally", ["Bill Bradley", "Sally"]),
            ("By: BOB", ["Bob"]),
            ("by: jimmy and JOHN", ["Jimmy", "John"])
        ]
        for comp in comparisons:
            self.assertEqual(parse_authors(comp[0]), comp[1])
