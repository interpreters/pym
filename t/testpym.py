# testpym.py: test pym
# Copyright (c) 2017 cxw42

import sys

# Get pym
sys.path.insert(0, '.')     # if cwd is pym/
sys.path.insert(0, '..')    # in case cwd is pym/t rather than pym
import pym

import unittest
from unittest import TestCase

class Basic(TestCase):
    """Basic tests"""
    def setUp(self):
        self.expressions=(  # for test_expressions
            ('<[2+2]>','4'),
            ("foo\n<['yes']>", "foo\nyes"),
        );

    def test_expressions(self):
        """ Expressions """
        for test in self.expressions:
            res = pym.pym_process_text(test[0])
            self.assertEqual(res, test[1])
    # end test_expressions()

if __name__ == '__main__':
    unittest.main()

# vi: set ts=4 sts=4 sw=4 et ai ff=unix: #
