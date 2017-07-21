# -*- coding: utf-8 -*-
"""
    sphinxtlisp.nodes
    ~~~~~~~~~~~~~~~~~

    Custom nodes for TLisp

    These are needed as lisp paramaters are space, not comma separated.
"""

from sphinx import addnodes

class tlisp_parameterlist(addnodes.desc_parameterlist):
    """Node for a lisp parameter list."""
    child_text_separator = ' '

class tlisp_parameter(addnodes.desc_parameter):
    """Node for a single lisp parameter."""
    pass
