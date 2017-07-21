# -*- coding: utf-8 -*-
"""
    sphinxtlisp.domain
    ~~~~~~~~~~~~~~~~~~

    The TLisp domain.

"""
import re

from docutils.parsers.rst import Directive, directives

from sphinx import addnodes
from sphinx.roles import XRefRole
from sphinx.locale import l_, _
from sphinx.domains import Domain, ObjType
from sphinx.domains.python import PyModulelevel
from sphinx.directives import ObjectDescription
from sphinx.util.nodes import make_refnode
from sphinx.util.docfields import Field, GroupedField, TypedField

from .nodes import tlisp_parameterlist, tlisp_parameter

# REs for TLisp signatures
tlisp_sig_re = re.compile(
    r'''^\(([\w+-/*@!<=>]+)\s*             # symbol name
          (?: (.*))? \)         # optional: arguments
          (?:\s* -> \s* (.*))?  # optional: return annotation
          $                     # and nothing more
          ''', re.VERBOSE)



class TLispExp(PyModulelevel): #ObjectDescription
    """
    Description of a TLisp expression.
    """
    option_spec = {
        'noindex': directives.flag,
        'module': directives.unchanged,
        'annotation': directives.unchanged,
    }

    doc_field_types = [
        TypedField('parameter', label=l_('Parameters'),
                   names=('param', 'parameter', 'arg', 'argument',
                          'keyword', 'kwarg', 'kwparam'),
                   typerolename='obj', typenames=('paramtype', 'type'),
                   can_collapse=True),
        Field('returnvalue', label=l_('Returns'), has_arg=False,
              names=('returns', 'return')),
        Field('returntype', label=l_('Return type'), has_arg=False,
              names=('rtype',)),
    ]

    def get_signature_prefix(self, sig):
        """May return a prefix to put before the object name in the
        signature.
        """
        return self.objtype + ' '

    def needs_arglist(self):
        """May return true if an empty argument list is to be generated even if
        the document contains none.
        """
        return False

    def handle_signature(self, sig, signode):
        """Transform a TLisp signature into RST nodes.

        Return (fully qualified name of the thing, classname if any).
        """
        m = tlisp_sig_re.match(sig)
        if m is None:
            raise ValueError
        name, arglist, retann = m.groups()
        name_prefix = None
        
        package = self.env.temp_data.get('tl:package')

        sig_prefix = self.get_signature_prefix(sig)
        if sig_prefix:
            signode += addnodes.desc_annotation(sig_prefix, sig_prefix)

        if name_prefix:
            signode += addnodes.desc_addname(name_prefix, name_prefix)
        
        anno = self.options.get('annotation')

        sexp = tlisp_parameterlist()
        sexp += addnodes.desc_name(name, name)
        
        for argument in arglist.split(' '):
            argument = argument.strip()
            sexp += tlisp_parameter(argument, argument)
        
        signode += sexp
        
        if retann:
            signode += addnodes.desc_returns(retann, retann)
        if anno:
            signode += addnodes.desc_annotation(' ' + anno, ' ' + anno)
        return name, name_prefix

    def get_index_text(self, modname, name):
        """Return the text for the index entry of the object."""
        if self.objtype == 'function':
            return _('%s (TLisp function)') % name[0]
        else:
            raise NotImplementedError("not a TLisp function")
            #return _('%s (TLisp %s)') % (name.split(":")[-1], type)

    def add_target_and_index(self, name, sig, signode):
        # node target
        fullname = 'tl.' + name[0].lower()
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            symbols = self.env.domaindata['tl']['symbols']
            if fullname in symbols:
                self.state_machine.reporter.warning(
                    'duplicate symbol description of %s, ' % fullname +
                    'other instance in ' + self.env.doc2path(symbols[fullname][0]),
                    line=self.lineno)
            symbols[fullname] = (self.env.docname, self.objtype)

        indextext = self.get_index_text(None, name)
        if indextext:
            self.indexnode['entries'].append(
                ('single', indextext, fullname, '', None)
            )


class TLispCurrentPackage(Directive):
    """This directive is just to tell Sphinx that we're documenting stuff
    in namespace foo.

    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        env.temp_data['tl:package'] = self.arguments[0].upper()
        #index_package(self.arguments[0].upper())
        return []


class TLispXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        if not has_explicit_title:
            target = target.lstrip('~')  # only has a meaning for the title
            # if the first character is a tilde, don't display the package
            if title[0:1] == '~':
                symbol = title[1:].split(':')
                package = symbol[0]
                title = symbol[-1]
                if target[0] == ":":
                    title = ":" + title
        return title, target


class TLispDomain(Domain):
    """TLisp language domain."""
    name = 'tl'
    label = 'TLisp'

    object_types = {
        'package':  ObjType(l_('package'),  'package', 'obj'),
        'function': ObjType(l_('function'), 'func', 'obj'),
        }

    directives = {
        'package': TLispCurrentPackage,
        'function': TLispExp,
    }

    roles = {
        'function': TLispXRefRole(),
        'obj': TLispXRefRole(),
    }
    initial_data = {
        'symbols': {},
    }

    def clear_doc(self, docname):
        for fullname, (fn, _l) in list(self.data['symbols'].items()):
            if fn == docname:
                del self.data['symbols'][fullname]

    def find_obj(self, env, name):
        """Find a Lisp symbol for "name", perhaps using the given package
        Return a list of (name, object entry) tuples.

        """
        # Case insensitive search, and strip parens
        name = name.strip('()').lower()
        if not name:
            return []

        symbols = self.data['symbols']
        name = 'tl.' + name
        # Only support exact matches for now
        if name in symbols:
            return [(name, symbols[name])]

    def resolve_xref(self, env, fromdocname, builder,
                     typ, target, node, contnode):
        matches = self.find_obj(env, target)
        if not matches:
            return None
        elif len(matches) > 1:
            logger.warning('more than one target found for cross-reference %r: %s',
                           target, ', '.join(match[0] for match in matches),
                           location=node)
        name, obj = matches[0]
        return make_refnode(builder, fromdocname, obj[0], name, contnode, name)

    def get_symbols(self):
        for refname, docs in self.data['symbols'].iteritems():
            for (docname, type) in docs:
                yield (refname, refname, type, docname, refname, 1)
