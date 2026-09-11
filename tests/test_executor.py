"""Code execution sandbox behaviour."""

import unittest

from constants import MAX_OUTPUT_CHARS
from executor import run_code, truncate_output


class TruncateOutputTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(truncate_output(''), '')
        self.assertEqual(truncate_output(None), '')

    def test_short_text_unchanged(self):
        self.assertEqual(truncate_output('hello'), 'hello')

    def test_long_text_is_capped(self):
        text = 'x' * (MAX_OUTPUT_CHARS + 10)
        result = truncate_output(text)
        self.assertTrue(result.startswith('x' * MAX_OUTPUT_CHARS))
        self.assertIn('output truncated', result)


class RunCodeTests(unittest.TestCase):
    def test_unsupported_language(self):
        result = run_code('print(1)', '', 1, 'javascript')
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'system_error')
        self.assertIn('Unsupported language', result['error'])

    def test_python_stdout(self):
        result = run_code('print(int(input()) + int(input()))', '1\n2', 2, 'python')
        self.assertTrue(result['success'])
        self.assertEqual(result['output'], '3')
        self.assertEqual(result['status'], 'success')

    def test_python_runtime_error(self):
        result = run_code('raise ValueError("nope")', '', 2, 'python')
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'runtime_error')
        self.assertIn('ValueError', result['error'])

    def test_python_timeout(self):
        result = run_code('import time\ntime.sleep(5)', '', 0.3, 'python')
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'time_limit')
        self.assertEqual(result['error'], 'Time Limit Exceeded')


if __name__ == '__main__':
    unittest.main()
