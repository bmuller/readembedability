import unittest

from readembedability.utils import longest_unique, flatten, URL


class UtilsTest(unittest.TestCase):
    def test_url_parse(self):
        # this was causing issues because the url param signature
        # was based on the order of the GET params which was getting
        # out of order on parse then str()
        surl = "https://i.reddituploads.com/fb4958d38bae4c438232b12863bb9b66"
        surl += "?fit=max&h=1536&w=1536&s=825971c281842f59dacb2d91e0b8347f"
        self.assertEqual(surl, str(URL(surl)))

    def test_url_unparse(self):
        surl = "https://blah.com/something"
        surl += "?fit=max&h=1536&w=1536&s=825971c281842f59dacb2d91e0b8347f"
        url = URL(surl).set_param('one', 'two').set_param('three', 'four')
        self.assertEqual(surl + '&one=two&three=four', str(url))

    def test_flatten(self):
        def flat(maybelist):
            return list(flatten(maybelist))

        inp = [[1, 2, 3], [[[[4]]]], [[5, 6]], 7]
        out = [1, 2, 3, 4, 5, 6, 7]
        self.assertEqual(flat(inp), out)
        self.assertEqual(flat(1), [1])
        self.assertEqual(flat([(1)]), [(1)])
        self.assertEqual(flat([1, [[2]]]), [1, 2])
        self.assertEqual(flat([1]), [1])

    def test_longest_unique(self):
        orig = ['one', 'One Two', 'two']
        self.assertEqual(longest_unique(orig), ['One Two'])

        orig = ['one', 'One Two', 'three']
        self.assertEqual(longest_unique(orig), ['One Two', 'three'])

        orig = ['three', 'One Two', 'two']
        self.assertEqual(longest_unique(orig), ['three', 'One Two'])

        orig = ['three']
        self.assertEqual(longest_unique(orig), ['three'])

        self.assertEqual(longest_unique([]), [])

        orig = ['One', 'Two']
        self.assertEqual(longest_unique(orig), ['One', 'Two'])

        orig = ['one', 'two', 'Three', 'three Four']
        self.assertEqual(longest_unique(orig), ['one', 'two', 'three Four'])
