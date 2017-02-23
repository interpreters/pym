# testpym.py: test pym
# Copyright (c) 2017 cxw42

import sys

# Get pym
sys.path.insert(0, '.')     # if cwd is pym/
sys.path.insert(0, '..')    # in case cwd is pym/t rather than pym
import pym

import unittest
from unittest import TestCase

class TestCaseChk(TestCase):
    """ Parent class defining utility functins """

    def chk(self, text, aim):
        res = pym.pym_process_text(text)
        self.assertEqual(res, aim)

class Basic(TestCaseChk):
    """Basic tests"""

    def test_2plus2(self): self.chk('<[2+2]>','4')
    def test_LiteralPlusExp(self): self.chk("foo\n<['yes']>", "foo\nyes")

    def test_IfTrueCond(self): self.chk("""#begin python
foo=42
#end python
#if foo==42
yes
#else
no
#fi""", "yes\n")

    def test_IfFalseCond(self): self.chk("""#begin python
foo=41
#end python
#if foo==42
yes
#else
no
#fi""", "no\n")

    def test_ElifCond(self): self.chk("""#begin python
foo=41
#end python
#if foo==42
yes
#elif foo==41
not forty-two
#else
no
#fi""", "not forty-two\n")

    def test_MultilineTrue(self): self.chk("""#if True
line1
line2
#endif""", "line1\nline2\n")

    def test_MultilineFalse(self): self.chk("""#if False
line1
line2
#endif""", "")

#end Basic(TestCaseChk)

class PymExceptionTest(TestCaseChk):
    """ Tests involving throwing Pym* exceptions """

    def test_EOF(self): self.chk("""#begin python
raise PymEndOfFile
#end python""", '')

    def test_Exit(self): self.chk("""#begin python
raise PymExit
#end python""", '')

#end PymExceptionTest(TestCaseChk)

if __name__ == '__main__':
    unittest.main()

# vi: set ts=4 sts=4 sw=4 et ai ff=unix: #
