# testpym.py: test pym
# Copyright (c) 2017 cxw42

import os, sys
import pdb

# Get pym
sys.path.insert(0, '.')     # if cwd is pym/
sys.path.insert(0, '..')    # in case cwd is pym/t rather than pym
import pym

import unittest
from unittest import TestCase

class TestCaseChk(TestCase):
    """ Parent class defining utility functins """

    def setUp(self):
        self.mypath = os.path.dirname(__file__)     # where this file is

    def p(self, fn):
        """ Make the path to _fn_ in the same directory as this file """
        return "'" + os.path.join(self.mypath, fn).replace("'", "\\'") + "'"

    def chk(self, text, aim, **env_overrides):
        res = pym.pym_process_text(text, **env_overrides)
        self.assertEqual(res, aim)

    def chkRaises(self, text, errmsg_regex, **env_overrides):
        def inner(text, env_overrides):
            return pym.pym_process_text(text, **env_overrides)

        self.assertRaisesRegexp(
                pym.PymProcessingError, errmsg_regex, inner,
                text, env_overrides     # args to _inner_
        )
    # end chkRaises()

######################################################################
class Basic(TestCaseChk):
    """Basic tests"""

    def test_2plus2(self): self.chk('<[2+2]>','4')

    def test_LiteralPlusExp(self): self.chk("foo\n<['yes']>", "foo\nyes")

    def test_IfTrueCond(self): self.chk(
"""#begin python
foo=42
#end python
#if foo==42
yes
#else
no
#fi""", "yes\n")

    def test_IfFalseCond(self): self.chk(
"""#begin python
foo=41
#end python
#if foo==42
yes
#else
no
#fi""", "no\n")

    def test_ElifCond(self): self.chk(
"""#begin python
foo=41
#end python
#if foo==42
yes
#elif foo==41
not forty-two
#else
no
#fi""", "not forty-two\n")

    def test_MultilineTrue(self): self.chk(
"""#if True
line1
line2
#endif""", "line1\nline2\n")

    def test_MultilineFalse(self): self.chk(
"""#if False
line1
line2
#endif""", "")

#end Basic(TestCaseChk)

######################################################################
class PymExceptionFromInput(TestCaseChk):
    """ Tests involving throwing PymEndOfFile and PymExit exceptions
        from input files. """

    def test_EOF(self): self.chk(
"""#begin python
raise PymEndOfFile
#end python""", '')

    def test_Exit(self): self.chk(
"""#begin python
raise PymExit
#end python""", '')

    def test_EOF_textbefore(self): self.chk(
"""foo
#begin python
raise PymEndOfFile
#end python""", "foo\n")

    def test_Exit_textbefore(self): self.chk(
"""bar
#begin python
raise PymExit
#end python""", "bar\n")

    def test_EOF_textafter(self): self.chk(
"""foo2
#begin python
raise PymEndOfFile
#end python
this shouldn't print""", "foo2\n")

    def test_Exit_textafter(self): self.chk(
"""bar2
#begin python
raise PymExit
#end python
this shouldn't print""", "bar2\n")

    # tests of throwing from included files

    def test_included_EOF(self): self.chk(
        '#include '+self.p('eof.txt'), "before eof\n")

    def test_included_Exit(self): self.chk(
        '#include '+self.p('exit.txt'), "before exit\n")

    def test_included_EOF_indirect(self): self.chk(
        '#include '+self.p('eof-indirect.txt'),
"""indirect before eof
before eof
indirect after eof
""")

    def test_included_Exit_indirect(self): self.chk(
        '#include '+self.p('exit-indirect.txt'),
"""indirect before exit
before exit
""")    # "indirect after exit" doesn't get printed

#end PymExceptionTest(TestCaseChk)

######################################################################
class PymCondPython(TestCaseChk):
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

######################################################################
class Include(TestCaseChk):
    """ Tests of #includes """

    def test_basic(self): self.chk('#include ' + self.p('plain.txt'),
                                    "Line 1\nLine 2\n")

    def test_expr(self): self.chk('#include '+self.p('expr.txt'),
                                    "42\n", foo=42)

    def test_block_and_expr(self):
        """ Modifying a value used in an #include before the #include """
        self.chk(
"""#begin python
foo = foo * 2
#end python
#include """+self.p('expr.txt'),
            "84\n",
            foo=42)

    def test_pyblock(self):
        """ pyblock sets a variable, which should be accessible outside
            since all includes are processed in the same environment. """
        self.chk("#include "+self.p('pyblock.txt')+
            "\n<[foo]>", "Inner message")

    def test_include_direct_expr(self):
        """ #include_direct of a file containing an expression -
            doesn't evaluate the expression. """
        self.chk('#include_direct '+self.p('expr.txt'), "<[foo]>\n")

    def test_include_direct_block(self):
        """ #include_direct of a file containing a Python block -
            doesn't evaluate the block. """
        self.chk('#include_direct '+self.p('pyblock.txt'),
"""#begin python
foo="Inner message"
#end python
""")

    def test_iterative_include(self):
        """ iterative_include.txt includes itself multiple times
            based on _count_.  The first output is one less than the
            initial _count_ because iterative_include.txt decrements first. """
        self.chk('#include '+self.p('iterative_include.txt'),
                "3\n2\n1\nzero\n",
                count = 4)

    def test_iterative_include_lots(self):
        """ iterative_include.txt, but more times
            based on _count_. """
        self.chk('#include '+self.p('iterative_include.txt'),
                "9\n8\n7\n6\n5\n4\n3\n2\n1\nzero\n",
                count=10)

######################################################################
class Elif(TestCaseChk):
    """ Tests of #elif """

    def setUp(self):
        self.foo_bar = (
"""#if foo
Foo
#elif bar
Bar
#else
Bat
#endif""")

        self.exprs=(
"""#if foo
<[14]>
#elif bar
<[28]>
#else
<[42]>
#endif""")

        self.blocks=(
"""#if foo
#begin python
def x(): return "Hello"
#end python
#elif bar
#begin python
def x(): return "World"
#end python
#else
#begin python
def x(): return "Spam"
#end python
#endif
<[x()]>""")     # also tests lack of a trailing newline

   #setUp()


    def test_foo_bar__foo(self): self.chk(self.foo_bar, "Foo\n",
            foo=True, bar=True)

    def test_foo_bar__bar(self): self.chk(self.foo_bar, "Bar\n",
            foo=False, bar=True)

    def test_foo_bar__bat(self): self.chk(self.foo_bar, "Bat\n",
            foo=False, bar=False)

    # exprs
    def test_exprs__foo(self): self.chk(self.exprs, "14\n",
            foo=True, bar=True)

    def test_exprs__bar(self): self.chk(self.exprs, "28\n",
            foo=False, bar=True)

    def test_exprs__bat(self): self.chk(self.exprs, "42\n",
            foo=False, bar=False)

    # blocks
    def test_blocks__foo(self): self.chk(self.blocks, "Hello",
            foo=True, bar=True)

    def test_blocks__bar(self): self.chk(self.blocks, "World",
            foo=False, bar=True)

    def test_blocks__bat(self): self.chk(self.blocks, "Spam",
            foo=False, bar=False)

#####################################################################

# TODO add tests of error conditions: nested #begin python blocks; missing
# #end python; #elif or #endif before #if; #endif before #if; misspelled
# command names (e.g., #elsif); commands without required arguments.

class BadParse(TestCaseChk):
    """ Tests of input that cannot be parsed. """

    def test_unterminated_python_block(self):
        self.chkRaises('#begin python','unterminated python code')

    def test_end_python_block_without_begin(self):
        self.chkRaises('#end python','superfluous end python')

#####################################################################
if __name__ == '__main__':
    unittest.main()

# vi: set ts=4 sts=4 sw=4 et ai ff=unix: #
