# -*- coding: utf-8 -*-
"""
    sphinxtlisp.tlisp
    ~~~~~~~~~~~~~~~~~

    The TLisp Function list parser.

"""
import re
import os.path
import traceback
import warnings
import textwrap
import sys
import imp

from six import string_types

from sphinx.util.console import bold
from sphinx.ext.napoleon.iterators import modify_iter
from sphinx.ext.napoleon.docstring import GoogleDocstring, _directive_regex, _google_section_regex

from .domain import tlisp_sig_re

_first_word_regex = re.compile(r'(\w+).*$')
_multispace_regex = re.compile(r'\s\s+')
_literal_regex = re.compile(r'(?<!\w)(\'\w+)(?![\w\'])')
_fnclink_regex = re.compile(r'([a-z]+[A-Z][a-z]+\w*)')

class TLispDocstring(GoogleDocstring):
    def __init__(self, docstring, config=None, sig=None, what='', name='',
               arglist='', retann='', allfuncs=[]):
        self._config = config

        if not what:
            what = 'function'

        if sig:
            name, arglist, retann = tlisp_sig_re.match(sig).groups()
            self.tlisp_signature = sig.strip()

        self._what = what
        self.name = name
        self.args = [arg.strip('[]') for arg in arglist.split()]
        self.retann = retann

        if isinstance(docstring, string_types):
            def lnkrepl(match):
                if match.group(1).lower() in allfuncs:
                    return ':tl:function:`'+match.group()+'`'
                else:
                    return match.group()
            docstring = _literal_regex.sub(r'``\1``', docstring)
            docstring = _fnclink_regex.sub(lnkrepl, docstring)
            docstring = docstring.splitlines()
        self._lines = docstring
        self._line_iter = modify_iter(docstring, modifier=lambda s: s.rstrip())
        self._parsed_lines = []  # type: List[unicode]
        self._is_in_section = False
        self._is_in_params = False
        self._param_fields = []
        self._section_indent = 0
        self._directive_sections = []
        self._sections = {
                'parameter': self._parse_parameter_section,
                'attributes': self._parse_attributes_section,
                'example': self._parse_examples_section,
                'examples': self._parse_examples_section,
                'keyword args': self._parse_keyword_arguments_section,
                'keyword arguments': self._parse_keyword_arguments_section,
                'methods': self._parse_methods_section,
                'note': self._parse_note_section,
                'notes': self._parse_notes_section,
                'other parameters': self._parse_other_parameters_section,
                'return': self._parse_returns_section,
                'returns': self._parse_returns_section,
                'raises': self._parse_raises_section,
                'references': self._parse_references_section,
                'see also': self._parse_see_also_section,
                'todo': self._parse_todo_section,
                'warning': self._parse_warning_section,
                'warnings': self._parse_warning_section,
                'warns': self._parse_warns_section,
                'yield': self._parse_yields_section,
                'yields': self._parse_yields_section,
                } # type: Dict[unicode, Callable]
        self._parse()
        self.__doc__ = str(self)


    def _is_section_header(self):
        self._is_in_params = False
        if super()._is_section_header():
            return True
        section = self._line_iter.peek()
        match = _first_word_regex.match(section)
        if match and match.group(1) in self.args:
            self._is_in_params = True
            return True
        return False

    def _consume_section_header(self):
        if self._is_in_params:
            return 'parameter'
        else:
            return super()._consume_section_header()

    def _parse_parameter_section(self, section):
        line = next(self._line_iter)
        _name =  _first_word_regex.match(line).group(1)
        remain = line.replace(_name,'', 1).strip()
        _type = ''
        _desc = ''
        if remain == ':':
            pass
        elif remain.startswith(': '):
            _type = remain[1:].strip()
        else:
            _desc = remain

        indent = self._get_indent(line) + 1
        _descs = [_desc] + self._dedent(self._consume_indented_block(indent))
        _descs = self.__class__(_descs, self._config).lines()

        self._param_fields.append((_name, _type, _descs,))
        return ['']

    def _parse(self):
        # type: () -> None
        self._parsed_lines = self._consume_empty()

        if self.name and (self._what == 'attribute' or self._what == 'data'):
            self._parsed_lines.extend(self._parse_attribute_docstring())
            return
        section = None
        while self._line_iter.has_next():
            if self._is_section_header():
                try:
                    section = self._consume_section_header()
                    self._is_in_section = True
                    self._section_indent = self._get_current_indent()
                    if _directive_regex.match(section):  # type: ignore
                        lines = [section] + self._consume_to_next_section()
                    else:
                        lines = self._sections[section.lower()](section)
                finally:
                    self._is_in_section = False
                    self._section_indent = 0
            else:
                if not self._parsed_lines:
                    lines = self._consume_contiguous() + self._consume_empty()
                else:
                    lines = self._consume_to_next_section()
                # check for tables
                lines = self._parse_extra(lines)
            if not self._is_in_params and self._param_fields:
                self._write_param_section()
            self._parsed_lines.extend(lines)
        if self._param_fields:
            self._write_param_section()

    def _parse_extra(self, content):
        """
        Parse a generic section of text and look for TLisp extras
        e.g. space separated tables
        """
        if not content:
            return content
        lines = []
        while content:
            line = content.pop(0)
            parts = _multispace_regex.split(line.strip())
            if len(parts) < 2:
                lines.append(line)
            else:
                desc = [parts]
                ncol = len(parts)
                width = [[len(p) for p in parts]]
                while content:
                    parts =_multispace_regex.split(content[0].strip())
                    if len(parts) == ncol:
                        content.pop(0)
                        desc.append(parts)
                        width.append([len(p) for p in parts])
                    else:
                        break
                if len(width) == 1:
                    width = width[0]
                else:
                    width = list(map(max,*width))
                lines.append(u'')
                lines.append(u'.. csv-table::')
                lines.append(u'    :widths: ' + ','.join(map(str,width)))
                lines.append(u'    :delim: \\')
                lines.append(u'')
                desc = ['\\'.join(parts) for parts in desc]
                lines.extend(self._indent(desc, 4))
        return lines

    def _format_fields(self, field_type, fields):
        # type: (unicode, List[Tuple[unicode, unicode, List[unicode]]]) -> List[unicode]
        field_type = ':%s:' % field_type.strip()
        lines = []
        lines += [field_type]  # type: List[unicode]
        lines += [u'']
        for _name, _type, _desc in fields:
            _desc = self._strip_empty(_desc)
            has_desc = any(_desc)
            if _name:
                if _type:
                    lines += self._indent(['**%s** : %s' % (_name, _type)])
                else:
                    lines += self._indent(['**%s**' % _name])
            elif _type:
                lines += self._indent(['%s' % _type])

            if has_desc:
                lines += [u'']
                lines += self._indent(self._fix_field_desc(_desc), 8)
            lines.append(u'')
        return lines


    def _write_param_section(self):
        if self._config.napoleon_use_param:
            lines = self._format_docutils_params(self._param_fields)
        else:
            lines = self._format_fields('Parameters', self._param_fields)
        self._parsed_lines.extend(lines)
        self._param_fields = []


def initialize(app):
    fn = app.config.tlisp_src
    if (fn and os.path.isfile(fn)):
        print("[tlisp] Parsing function list from", fn, "...")
        functions = parse_function_list(fn, app)
        app.config._tlispfuncs = functions

def parse_function_list(fnc_file, app):
    """
    Parse the Transcendence function list and import as dummy Python functions
    """
    funclist = []
    allnames = []
    class Obj:
        pass
    obj = None
    with open(fnc_file) as fh:
        for line in fh:
            m = tlisp_sig_re.match(line)
            if m:
                # We have a new function
                obj = Obj()
                obj.sig = line
                obj.doc = ''
                funclist.append(obj)
                allnames.append(m.group(1).lower())
            elif obj:
                obj.doc += line

    funclist = [TLispDocstring(f.doc, app.config, what='function', sig=f.sig, allfuncs=allnames) for f in funclist]
    fd = {f.name.lower(): f for f in funclist}

    #for key, obj in funcdict.items():
    #    obj.translate_docstring(app.config, funcdict)
    #mod = imp.new_module('tlisp')
    #sys.modules['tlisp'] = mod
    #for key, obj in funcdict.items():
    #    obj.__module__ = mod
    #    setattr(mod, obj.__name__, obj)

    return fd
