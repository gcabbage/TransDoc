# -*- coding: utf-8 -*-
"""
    sphinxtlisp.writers
    ~~~~~~~~~~~~~~~~~~~
    docutils writers handling custom TLisp nodes.
"""

from docutils import nodes

def noop(self, node):
    pass

def visit_html_parameter(self, node):
    # type: (nodes.Node) -> None
    if self.first_param:
        self.first_param = 0
    self.body.append(self.param_separator)
    if self.optional_param_level == 0:
        self.required_params_left -= 1
    if not node.hasattr('noemph'):
        self.body.append('<em>')

def depart_html_parameter(self, node):
    # type: (nodes.Node) -> None
    if not node.hasattr('noemph'):
        self.body.append('</em>')

def visit_latex_parameter(self, node):
    # type: (nodes.Node) -> None
    if self.first_param:
        self.first_param = 0
    self.body.append(self.param_separator)
    if not node.hasattr('noemph'):
        self.body.append(r'\emph{')

def depart_latex_parameter(self, node):
    # type: (nodes.Node) -> None
    if not node.hasattr('noemph'):
        self.body.append('}')

def visit_texinfo_parameter(self, node):
    # type: (nodes.Node) -> None
    if self.first_param:
        self.first_param = 0
    self.body.append(self.param_separator)
    text = self.escape(node.astext())
    # replace no-break spaces with normal ones
    text = text.replace(u' ', '@w{ }')
    self.body.append(text)
    raise nodes.SkipNode

def visit_text_parameter(self, node):
    # type: (nodes.Node) -> None
    if self.first_param:
        self.first_param = 0
    self.add_text(' ')
    self.add_text(node.astext())
    raise nodes.SkipNode


def redirect(nodetype):
    """
    Create wrapper function to reuse writers for another node type

    nodetype is the class whose visitor functions we want to reuse
    """
    name = nodetype.__name__
    v = lambda self, node: getattr(self, 'visit_'+name)(node)
    d = lambda self, node: getattr(self, 'depart_'+name)(node)
    return v, d
