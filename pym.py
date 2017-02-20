#!/usr/bin/env python
##
## pym 1.2, by Robert F. Tobler, 10-Mar-2002
##

import sys
import os
import string
import time

start_time = time.clock()

class PymException(Exception): pass
class PymEndOfFile(PymException): pass
class PymExit(PymException): pass

PYM_PATH = []
PYM_PREFIX_MAP = { '/': ("/","END_") }	# This translates a prefix so that
                                        # special macro names can be used:
                                        # e.g <[/KEY]> => <[END_KEY]>
                                        # Prefixes must be recognizable by
                                        # their 1st character (key in map).
PYM_EXPRESSION = ["<[","]>"]

ENVIRONMENT = {
    "PYM_EXPRESSION": PYM_EXPRESSION,
    "PYM_PREFIX_MAP": PYM_PREFIX_MAP,
    "PYM_PATH": PYM_PATH,
    "PymException": PymException,   	## mirror the exceptions in pym
    "PymEndOfFile": PymEndOfFile,   	## environment
    "PymExit": PymExit,
}

HTTP_HEADER = """Content-type: text/html

"""

HTTP_FOOTER = """
<!-- pym timings: %g sec rendering, %g sec overall -->
"""

def pym_error(message, loc):
    print "ERROR:", message, "in '%s'.", loc[0]
    sys.exit(-1)

def pym_expand(text, env, loc, out):
    (begin,end) = PYM_EXPRESSION
    prefix_map = PYM_PREFIX_MAP
    begin_len = len(begin)
    end_len = len(end)
    if len(text) <= begin_len + end_len:
    	out.append(text)
    else:
	pos = 0
	start = string.find(text, begin, pos)
	while (start >= 0):
    	    stop = string.find(text, end, start+begin_len)
	    if stop < 0: pym_error("unterminated python macro", loc)
	    out.append(text[pos:start])
	    exp = string.strip(text[start+begin_len:stop])
    	    prefix = prefix_map.get(exp[0])
	    try:
    		if prefix:
	    	    len_pr = len(prefix[0])
		    if len(exp) >= len_pr and exp[:len_pr] == prefix[0]:
	    		value = eval(prefix[1]+exp[len_pr:], env, env)
		    else:
			pym_error("illegal prefix '%s'" % exp[:len_pr], loc)
		else:
	    	    value = eval(exp, env, env)
	    except PymException: raise
	    except NameError: raise 	# doesn't have lineno
	    except KeyError: raise  	# ditto
	    except ImportError: raise   	# ..
	    except AttributeError: raise   	# ditto
	    except TypeError: raise   	# ditto
	    except Exception, error:
		error.filename = loc[0]
		error.lineno = error.lineno + loc[1] + \
		    	       len(string.split(text[0:start],'\n'))
		raise
    	    pym_expand(str(value), env, loc, out)
	    pos = stop+end_len
	    start = string.find(text, begin, pos)
	out.append(text[pos:])

def pym_read_file(filename, out):
    file = open(filename,"r")
    out.append(file.read())
    file.close()

def pym_expand_file(filename, env, out):
    file = open(filename,"r")
    text = file.read()
    file.close()
    lnum = 1
    py_pos = -1
    tx_pos = 0
    loc = (filename, 0)
    pos = 0
    cond = 1
    condstack = []
    lines = string.split(text, '\n')
    if len(lines[0]) > 2 and lines[0][:2] == "#!":
    	lines = lines[1:]
	lnum = 2
    for line in lines:
    	end = pos + len(line) + 1
	if line and line[0] == '#':
	    if tx_pos >= 0:
	    	tx_start = tx_pos ; tx_pos = -1
	    	try:
		    if cond:
		    	pym_expand(text[tx_start:pos], env, loc, out)
		except PymEndOfFile: break
	    if string.find(line,"end python") > 0:
    		if py_pos < 0: pym_error("superfluous end python", loc)
		if cond:
		    try:
			exec text[py_pos:pos] in env, env
		    except PymExit: raise
    	    	    except PymEndOfFile:
			py_pos = -1
			break
		    except NameError: raise 	# doesn't have lineno
		    except KeyError: raise  	# ditto
		    except ImportError: raise   # ditto
		    except AttributeError: raise    # ditto
		    except TypeError: raise   	# ditto
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
	    	if cond:
        	    dir = os.path.dirname(filename)
		    include = eval(string.strip(line[namestart:]), env, env)
		    includefilename = os.path.join(dir,include)
		    if not os.path.isfile(includefilename):
	    		for dir in PYM_PATH:
			    includefilename = os.path.join(dir, include)
			    if os.path.isfile(includefilename): break
		    if namestart == 8:
	    	    	pym_expand_file(includefilename, env, out)
		    else:
		    	pym_read_file(includefilename, out)
		tx_pos = end
		loc = (filename, lnum)
	    elif string.find(line, "if") == 1:
	    	condstack.append(cond)
	    	cond = eval(string.strip(line[3:]), env, env)
		tx_pos = end
		loc = (filename, lnum)
	    elif string.find(line, "elif") == 1:
	    	cond = eval(string.strip(line[5:]), env, env)
		tx_pos = end
		loc = (filename, lnum)
	    elif string.find(line, "else") == 1:
	    	cond = not cond
		tx_pos = end
		loc = (filename, lnum)
	    elif string.find(line, "endif") == 1:
	    	cond = condstack.pop()
		tx_pos = end
		loc = (filename, lnum)
	pos = end
	lnum = lnum + 1

    if py_pos >= 0: pym_error("unterminated python code", loc)
    len_text = len(text)
    if tx_pos >= 0 and tx_pos < len_text:
	try: pym_expand(text[tx_pos:min(pos,len_text)], env, loc, out)
	except PymEndOfFile: pass

if __name__ == '__main__':
    document_root = os.environ.get("DOCUMENT_ROOT")
    if not document_root:
	if len(sys.argv) == 1:
	    file_list = os.listdir('.')
	else:
	    file_list = []
	    incl = 0
	    for arg in sys.argv[1:]:
	    	if arg == '-I':
		    incl = 1
		    continue
		if incl:
		    if (arg[0] != '/'):
		    	arg = os.path.join(os.getcwd(), arg)
		    PYM_PATH.append(arg)
		    incl = 0
		    continue
		file_list.append(arg)
	if len(file_list) > 1:
	    talk = 1
	else:
	    talk = 0
	for filepath in file_list:
	    if len(filepath) > 4 and filepath[-4:] == '.pym':
		env = ENVIRONMENT.copy()
		out = []
		try:
    		    pym_expand_file(filepath, env, out)
		except PymExit: pass
		extension = env.get("PYM_EXTENSION","")
		if extension:
    		    file = open(filepath[:-4] + extension, "w")
		    for text in out: file.write(text)
    		    file.close()
		    if talk: print filepath
		else:
	    	    for text in out: sys.stdout.write(text)
    else:
	env = ENVIRONMENT.copy()
	PYM_PATH.append(document_root)
	path_translated = os.environ.get("PATH_TRANSLATED")
	sys.stdout.write(HTTP_HEADER)
	out = []
	try:
	    pym_expand_file(path_translated, env, out)
	except PymExit:
    	    pass
	for text in out: sys.stdout.write(text)
	if env.get("PYM_ARG_MAP",{}).get("debug","") == "timing":
	    overall = time.clock()
	    rendering = overall - start_time
	    sys.stdout.write(HTTP_FOOTER % (rendering, overall))
##
## end of PYM source
##
