import unittest
import re

from main import escape_text

class TestEscapeTextFunction(unittest.TestCase):

    def test_escape_special_characters(self):
        self.assertEqual(escape_text('--#===abcd'), r'\-\-\#\=\=\=abcd')

    def test_no_special_characters(self):
        self.assertEqual(escape_text('abcd'), 'abcd')

    def test_mixed_characters(self):
        self.assertEqual(escape_text('ab-cd_ef*gh'), r'ab\-cd\_ef\*gh')

    def test_escaped_characters(self):
        self.assertEqual(escape_text(r'\*\[\]'), r'\*\[\]')

    def test_combined_special_characters(self):
        self.assertEqual(escape_text('--#===abcd_*[()]'), r'\-\-\#\=\=\=abcd\_\*\[\(\)\]')

    def test_double_escaped_characters(self):
        self.assertEqual(escape_text(r'\\_\\*\\#'), r'\\_\\*\\#')

    def test_empty_string(self):
        self.assertEqual(escape_text(''), '')

    def test_only_special_characters(self):
        self.assertEqual(escape_text('_*[]()~`>#'), r'\_\*\[\]\(\)\~\`\>\#')

if __name__ == '__main__':
    unittest.main()
