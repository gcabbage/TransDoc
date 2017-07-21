# -*- coding: utf-8 -*-

"""
A Sphinx extension to document Transcendence
"""

from six import PY2, iteritems

from sphinx import addnodes
from sphinx.ext.napoleon import Config

from .domain import TLispDomain
from .nodes import tlisp_parameterlist, tlisp_parameter
from .autodoc import TLispDocumenter, TLispAutoDirective
from .tlisp import initialize
from .writer import *
from .autosummary import TLispSummary

def setup(app):
    app.add_domain(TLispDomain)
    app.add_node(tlisp_parameterlist,
                 html=redirect(addnodes.desc_parameterlist),
                 latex=redirect(addnodes.desc_parameterlist),
                 texinfo=redirect(addnodes.desc_parameterlist),
                 text=redirect(addnodes.desc_parameterlist))
    app.add_node(tlisp_parameter,
                 html=(visit_html_parameter, depart_html_parameter), #direct(addnodes.desc_parameter),
                 latex=(visit_latex_parameter, depart_latex_parameter),
                 texinfo=(visit_texinfo_parameter, noop),
                 text=(visit_text_parameter, noop))

    app.add_autodocumenter(TLispDocumenter)

    for name, (default, rebuild) in iteritems(Config._config_values):
        app.add_config_value(name, default, rebuild)

    TLispDomain.directives.update(autodoc=TLispAutoDirective)
    app.connect('builder-inited', initialize)
    app.add_config_value('tlisp_src', 'function_list.txt', True)

    app.add_directive('tlispsummary', TLispSummary)
