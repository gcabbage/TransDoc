# -*- coding: utf-8 -*-

"""
Extract TLisp API data from Debug.log
"""

import re
import os
import os.path
import argparse

from sphinx.util import rst

func_map = {
    "!="   : "_ne",
    "*"    : "_mul",
    "+"    : "_add",
    "-"    : "_sub",
    "/"    : "_div",
    "<"    : "_lt",
    "<="   : "_leq",
    "="    : "_eq",
    ">"    : "_gr",
    ">="   : "_geq",
    "@"    : "_at",
    "set@" : "_setat",
    "v*"   : "_vscl",
    "v+"   : "_vadd",
    "v->"  : "_vget",
    "v<-"  : "_vset",
    "v="   : "_vcmp",
    "v^"   : "_vmul",
    }

# automodule options
if 'SPHINX_APIDOC_OPTIONS' in os.environ:
    OPTIONS = os.environ['SPHINX_APIDOC_OPTIONS'].split(',')
else:
    OPTIONS = [
        #'members',
        #'undoc-members',
        # 'inherited-members', # disabled because there's a bug in sphinx
        #'show-inheritance',
        ]

debuglog_re = re.compile(r'^(?:\d\d/\d\d/\d\d\d\d\s\d\d\:\d\d\:\d\d\t)?(.*)$', re.VERBOSE)
alphanum_re = re.compile(r'^\w+$')

def format_heading(level, text, escape=True):
    # type: (int, unicode, bool) -> unicode
    """Create a heading of <level> [1, 2 or 3 supported]."""
    if escape:
        text = rst.escape(text)
    underlining = ['=', '-', '~', ][level - 1] * len(text)
    return '%s\n%s\n\n' % (text, underlining)


def format_directive(name):
    # type: (unicode, unicode) -> unicode
    """Create the automodule directive and add the options."""
    directive = '.. autotlisp:: %s\n' % name
    for option in OPTIONS:
        directive += '    :%s:\n' % option
    return directive


def parse_log(logfile, outfile="function_list.txt"):
    symbols = {}
    mode = None
    outf = open(outfile, "w")
    with open(logfile) as fh:
        for l in fh:
            # Strip the timestamp if present
            try:
                line = debuglog_re.match(l).groups()[0]
            except:
                print(l)
                raise
            
            if not mode:
                if line == ";Symbol List":
                    mode = "list"
                    next(fh)
                elif line ==";Function Help":
                    mode = "help"
                    next(fh)
            elif mode == "list":
                if line.startswith(";###"):
                    mode = None
                else:
                    parts = line.split()
                    stype = parts[1].strip(":")
                    if stype not in symbols:
                        symbols[stype] = []
                    symbols[stype].append(parts[0])
            elif mode == "help":
                if line.startswith(";###"):
                    mode = "done"
                else:
                    outf.write(line + "\n")
    outf.close()
    return symbols

def write_file(path, name, text):
    fname = os.path.join(path, "%s.%s" % (name, "rst"))
    with open(fname, "w") as f:
        f.write(text)


def main():
    symbols = parse_log("../../Debug.log")
    
    os.makedirs("source/autogen", exist_ok=True)
    for name in symbols['builtin']:
        text = format_heading(1, name)
        text += format_directive("(%s)"%name)

        if name in func_map:
            write_file("source/autogen", func_map[name], text)
        elif alphanum_re.match(name):
            write_file("source/autogen", name, text)
        else:
            print (name)
        
if __name__ == "__main__":
    main()
