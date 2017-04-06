#!/usr/bin/env python
## pym - revised by cxw42@github - devwrench.com
## Based on pym 1.2, by Robert F. Tobler, 10-Mar-2002
##

import sys
import os
import string
import time

start_time = time.clock()

class PymException(Exception): pass
class PymEndOfFile(PymException): pass      # For use by text being processed
class PymExit(PymException): pass           # ditto

class PymProcessingError(PymException): pass
    # For reporting errors that pym detects in the input.

# Default values of system variables
PYM_PATH = []
PYM_PREFIX_MAP = { '/': ("/","END_") }  # This translates a prefix so that
                                        # special macro names can be used:
                                        # e.g <[/KEY]> => <[END_KEY]>
                                        # Prefixes must be recognizable by
                                        # their 1st character (key in map).
PYM_EXPRESSION = ["<[","]>"]

# The default environment
ENVIRONMENT = {
    "PYM_EXPRESSION": PYM_EXPRESSION,
    "PYM_PREFIX_MAP": PYM_PREFIX_MAP,
    "PYM_PATH": PYM_PATH,
    "PymException": PymException,       ## mirror the exceptions in pym
    "PymEndOfFile": PymEndOfFile,       ## environment
    "PymExit": PymExit,
}

def pym_die(message, loc):
    """ Convenience function for reporting fatal parsing errors. """
    raise PymProcessingError(
        "%s in '%s' at %d."%(message, loc[0], loc[1])
    )
# end pym_die

def pym_expand_expressions(text, env, loc, out):
    """ Expand inline expressions in _text_ in environment _env_.
        Append the result to list _out_. """

    (begin,end) = PYM_EXPRESSION    # TODO get PYM_* from _env_ instead
    prefix_map = PYM_PREFIX_MAP
    begin_len = len(begin)
    end_len = len(end)

    if len(text) <= begin_len + end_len:
        out.append(text)
    else:
        pos = 0
        start = string.find(text, begin, pos)

        # TODO check for ]> without preceding <[ ?
        while (start >= 0):
            stop = string.find(text, end, start+begin_len)
            if stop < 0: pym_die("unterminated python macro", loc)
            out.append(text[pos:start])
            exp = string.strip(text[start+begin_len:stop])
            prefix = prefix_map.get(exp[0])
            try:
                if prefix:
                    len_pr = len(prefix[0])
                    if len(exp) >= len_pr and exp[:len_pr] == prefix[0]:
                        value = eval(prefix[1]+exp[len_pr:], env, env)
                    else:
                        pym_die("illegal prefix '%s'" % exp[:len_pr], loc)
                else:
                    value = eval(exp, env, env)
            except PymException: raise
            except NameError: raise         # doesn't have lineno
            except KeyError: raise          # ditto
            except ImportError: raise       # ..
            except AttributeError: raise    # ditto
            except TypeError: raise         # ditto
            except Exception, error:
                error.filename = loc[0]
                error.lineno = error.lineno + loc[1] + \
                               len(string.split(text[0:start],'\n'))
                raise

            pym_expand_expressions(str(value), env, loc, out)

            pos = stop+end_len
            start = string.find(text, begin, pos)
        #end while start>0

        out.append(text[pos:])
# end pym_expand_expressions()

def pym_dump_file_contents(filename, out):
    """ Append the contents of _filename_ to list _out_. """
    file = open(filename,"r")
    out.append(file.read())
    file.close()
# end pym_dump_file_contents()

def pym_expand_file(filename, env, out):
    """ Process the contents of _filename_ in environment _env_.
        Append the result to list _out_.
        A filename of '' means use standard input. """
    if filename=="":    fd = sys.stdin
    else:               fd = open(filename,"r")

    text = fd.read()

    if filename != "": fd.close()   # don't close stdin

    pym_expand_string(filename, text, env, out)
# end pym_expand_file()

def pym_expand_string(filename, text, env, out, command_char='#'):
    """ Process the (possibly multi-line) string _text_ in environment _env_.
        Append the result to list _out_. """
    # TODO add option to output a leader plus "##<loc>" at each line,
    # so the output lines can be automatically mapped to the input lines.
    lnum = 1
    py_pos = -1
    tx_pos = 0      # start of normal text
    loc = (filename, 0)
    pos = 0

    # Whether the current block is being evaluated, based on #if
    cond = True
    condstack = []

    # Whether we have already seen a True result in the current #if..elif..
    succeeded = False
    succeeded_stack = []

    # Process input
    lines = string.split(text, '\n')

    # Skip shebang, if any
    if len(lines[0]) > 2 and lines[0][:2] == '#!':
        lines = lines[1:]
        lnum = 2

    for line in lines:      # main loop
        end = pos + len(line) + 1

        if line and line[0] == command_char:        # a command

            if tx_pos >= 0:         # first, expand any text we've seen so far
                tx_start = tx_pos ; tx_pos = -1
                try:
                    if cond and all(condstack):
                        pym_expand_expressions(text[tx_start:pos],
                                                env, loc, out)
                except PymEndOfFile: break

            # Now process the command
            if string.find(line,"end python") > 0:
                if py_pos < 0: pym_die("superfluous end python", loc)

                if cond and all(condstack):
                    # Run the Python code unless it is excluded by an #if test
                    try:
                        exec text[py_pos:pos] in env, env
                        # TODO? in the future, maybe capture output from
                        # this block and add it to out[]?
                        # Presently, the _exec_ block cannot add lines to out.
                    except PymExit: raise
                    except PymEndOfFile:
                        py_pos = -1
                        break
                    except NameError: raise         # doesn't have lineno
                    except KeyError: raise          # ditto
                    except ImportError: raise       # ditto
                    except AttributeError: raise    # ditto
                    except TypeError: raise         # ditto
                    except Exception, error:
                        error.filename = loc[0]
                        error.lineno = error.lineno + loc[1]
                        raise
                py_pos = -1
                tx_pos = end

            elif string.find(line, "begin python") > 0:
                py_pos = end
                loc = (filename, lnum)

            elif string.find(line, "include") == 1:
                namestart = 8
                if string.find(line, "include_direct") == 1:
                    namestart = 15

                if cond and all(condstack):
                    dir_name = os.path.dirname(filename)
                        # First, try relative to the file we are currently
                        # processing (_filename_)
                    include = eval(string.strip(line[namestart:]), env, env)
                    includefilename = os.path.join(dir_name,include)

                    if not os.path.isfile(includefilename):
                        for dir_name in PYM_PATH:
                            includefilename = os.path.join(dir_name, include)
                            if os.path.isfile(includefilename): break
                        # TODO? Fail if the file could not be found?

                    if namestart == 8:  # #include
                        pym_expand_file(includefilename, env, out)
                    else:               # #include_direct
                        pym_dump_file_contents(includefilename, out)
                #endif conditions are true

                tx_pos = end
                loc = (filename, lnum)

            elif string.find(line, "if") == 1:

                condstack.append(cond)
                cond = bool(eval(string.strip(line[3:]), env, env))

                succeeded_stack.append(succeeded)
                succeeded = cond    # whether this #if succeeded

                tx_pos = end
                loc = (filename, lnum)

            # TODO die on #elif after #else
            elif string.find(line, "elif") == 1:
                if len(condstack)==0:
                    pym_die("#elif without #if", loc)

                if succeeded:   # Don't run this if an earlier clause won
                    cond = False
                else:
                    cond = bool(eval(string.strip(line[5:]), env, env))
                    succeeded = cond

                tx_pos = end
                loc = (filename, lnum)

            elif string.find(line, "else") == 1:
                if len(condstack)==0:
                    pym_die("#else without #if", loc)

                cond = not succeeded    # true if nothing else matched
                succeeded = True
                tx_pos = end
                loc = (filename, lnum)

            elif string.find(line, "endif") == 1:
                if len(condstack)==0:
                    pym_die("#endif without #if", loc)

                cond = condstack.pop()
                succeeded = succeeded_stack.pop()

                tx_pos = end
                loc = (filename, lnum)
        #endif the line was a command

        pos = end
        lnum = lnum + 1
    # next line

    if py_pos >= 0: pym_die("unterminated python code", loc)
    len_text = len(text)
    if tx_pos >= 0 and tx_pos < len_text:
        try:
            pym_expand_expressions(text[tx_pos:min(pos,len_text)], env, loc, out)
        except PymEndOfFile:
            pass
# end pym_expand_string()

def pym_process_text(text, **env_overrides):
    """ Preprocesses the complete file _text_ and returns the resulting string.
        If _env_overrides_ is provided, applies it to the environment
        before processing. """

    env = ENVIRONMENT.copy()        # each file has its own env
    env.update(env_overrides)
    out = []                        # list of expanded lines

    try:        # Do the processing
        pym_expand_string('', text, env, out)
    except PymExit:     # PymExit terminates processing of the string.
        pass

    return ''.join(out)
        # Newlines are expressly included in _out_, so we join on ''
        # instead of "\n".
# end pym_process_text()

def pym_command_line_main():
    file_list = []

    if len(sys.argv) > 1:   # arg(s) given - parse the command line
        file_list = []
        incl = False        # whether the next argument is an include path
        for arg in sys.argv[1:]:
            if arg == '-I':
                incl = True
                continue

            if incl:
                if (arg[0] != '/'):
                    arg = os.path.join(os.getcwd(), arg)
                PYM_PATH.append(arg)
                incl = False
                continue

            file_list.append(arg)
        # next arg
    #endif one argument

    # Set options
    if len(file_list) > 1:
        print_file_banners = True
    else:
        print_file_banners = False

    if len(file_list) == 0:
        file_list = [""]      # stdin

    # === Main loop ===
    for filepath in file_list:
        env = ENVIRONMENT.copy()        # each file has its own env
        out = []                        # list of expanded lines

        try:        # Do the processing
            pym_expand_file(filepath, env, out)
        except PymExit:     # PymExit terminates processing of that file
            pass            # even from deeply-nested includes.

        # Print the results
        if print_file_banners: print('=== %s ==='%filepath)
        for text in out:
            sys.stdout.write(text)
    # next filepath
# end pym_command_line_main()

if __name__ == '__main__':
    pym_command_line_main()

# vi: set ts=4 sts=4 sw=4 et ai ff=unix: #
