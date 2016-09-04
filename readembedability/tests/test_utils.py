import unittest

from readembedability.utils import longest_unique


class UtilsTest(unittest.TestCase):
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
