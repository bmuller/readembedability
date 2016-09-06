import unittest

from readembedability.utils import longest_unique, flatten


class UtilsTest(unittest.TestCase):
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
