# testpym.py: test pym
# Copyright (c) 2017 cxw42

import sys
import pdb

# Get pym
sys.path.insert(0, '.')     # if cwd is pym/
sys.path.insert(0, '..')    # in case cwd is pym/t rather than pym
import pym

import unittest
from unittest import TestCase

class TestCaseChk(TestCase):
    """ Parent class defining utility functins """

    def chk(self, text, aim, **env_overrides):
        res = pym.pym_process_text(text, **env_overrides)
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

    def test_EOF_textbefore(self): self.chk("""foo
#begin python
raise PymEndOfFile
#end python""", "foo\n")

    def test_Exit_textbefore(self): self.chk("""bar
#begin python
raise PymExit
#end python""", "bar\n")

    def test_EOF_textafter(self): self.chk("""foo2
#begin python
raise PymEndOfFile
#end python
this shouldn't print""", "foo2\n")

    def test_Exit_textafter(self): self.chk("""bar2
#begin python
raise PymExit
#end python
this shouldn't print""", "bar2\n")

    # TODO add tests throwing from included files

#end PymExceptionTest(TestCaseChk)

class PymCondPythonTest(TestCaseChk):
    """ Tests involving Python blocks guarded by conditionals """

    def setUp(self):
        self.msg_1_level = """#if inp
#begin python
foo=42
#end python
#else
#begin python
foo=84
#end python
#endif
<[foo]>"""

        self.msg_2_levels = """<[inp1]>
<[inp2]>
#if inp1
#if inp2
#begin python
foo='1T2T'
#end python
#else
#begin python
foo='1T2F'
#end python
#endif
#else
#if inp2
#begin python
foo='1F2T'
#end python
#else
#begin python
foo='1F2F'
#end python
#endif
#endif
<[foo]>"""


    def test_assignment_True(self):
        self.chk(self.msg_1_level, '42', inp=True)

    def test_assignment_False(self):
        self.chk(self.msg_1_level, '84', inp=False)

    def test_assignment_TT(self):
        self.chk(self.msg_2_levels, "True\nTrue\n1T2T", inp1=True, inp2=True)

    def test_assignment_TF(self):
        #pdb.set_trace()
        self.chk(self.msg_2_levels, "True\nFalse\n1T2F", inp1=True, inp2=False)

    def test_assignment_FT(self):
        self.chk(self.msg_2_levels, "False\nTrue\n1F2T", inp1=False, inp2=True)

    def test_assignment_FF(self):
        self.chk(self.msg_2_levels, "False\nFalse\n1F2F", inp1=False, inp2=False)


#####################################################################
if __name__ == '__main__':
    unittest.main()

# vi: set ts=4 sts=4 sw=4 et ai ff=unix: #
