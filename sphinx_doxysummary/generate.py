#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 01:29:08 2022

@author: quocdang
"""

import os
import re

from typing import Any, Dict, List, Tuple, Set

from jinja2 import TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.ext.autosummary.generate import _underline
from sphinx.ext.autosummary import get_rst_suffix
from sphinx.locale import __
from sphinx.util import logging, rst
from sphinx.util.osutil import ensuredir
from sphinx.util.template import SphinxTemplateLoader

from sphinx_doxysummary.utils import split_name, fullname_to_filename
from sphinx_doxysummary.xmltree import xml_tree

logger = logging.getLogger(__name__)

class DoxySummaryEntry:

    def __init__(self, filename: str, name: str,
                 template: str= 'cppbase.rst', toctree: str = '',
                 scope: str = ''):
        """Simple class representing an entry in \"doxysummary\" directive.

        Parameters
        ----------
        filename : str
            Name of the rst file containing the entry.
        template : str
            Name of template for generating the entry.
        name : str
            Content of the entry.
        toctree : str, optional
            Directory to generate automatically rst files.
            The default is ''.
        scope : str, optional
            Current scope of the entry.
            The default is ''.

        Notes:
        The argument in the name saved to the entry is removed. Only the
        function name and the function arguments are retained.
        """
        self.filename = filename
        self.toctree = toctree
        self.template = template
        self.name = name
        self.scope = scope

    @property
    def fullname(self) -> str:
        """
        Get the fullname (scope + name) of the entry.

        Return
        ------
        str
            Fullname of the entry.
        """
        splitted_name = split_name(self.name)
        if self.scope != '':
            splitted_name[1] = '::'.join([self.scope, splitted_name[1]])
        return ''.join([name for name in splitted_name if name != ''])

    def __repr__(self):
        return f'Entry of name {self.fullname} template {self.template}'


class DoxySummaryRenderer:

    def __init__(self, app: Sphinx) -> None:
        """
        Renderer generated rst files based on templates.

        Parameters
        ----------
        app : Sphinx
            Sphinx application.

        Raises
        ------
        ValueError
            When ``app`` is not a sphinx.Builder.
        """
        if isinstance(app, Builder):
            raise ValueError('Expected a Sphinx application object!')

        package_templates_path = os.path.normpath(os.path.join(__file__, '..'))
        package_templates_path = [os.path.join(package_templates_path,
                                               'templates')]
        loader = SphinxTemplateLoader(app.srcdir, app.config.templates_path,
                                      package_templates_path)

        self.env = SandboxedEnvironment(loader=loader)
        self.env.filters['escape'] = rst.escape
        self.env.filters['e'] = rst.escape
        self.env.filters['underline'] = _underline

        if app.translator:
            self.env.add_extension("jinja2.ext.i18n")
            self.env.install_gettext_translations(app.translator)

    def render(self, template_name: str, context: Dict) -> str:
        """
        Render a string based on a template.

        Parameters
        ----------
        template_name : str
            File name of the template (with respect to
            ``package_templates_path``).
        context : Dict
            Python ``dict`` of keyword-value to be fetched in the template.

        Return
        ------
        str
            Content of th template with matched keywords.
        """
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            try:
                # objtype is given as template_name
                template = self.env.get_template(f'autosummary/'
                                                 f'{template_name}.rst')
            except TemplateNotFound:
                # fallback to base.rst
                template = self.env.get_template('autosummary/base.rst')

        return template.render(context)

def process_generate_files(app: Sphinx) -> None:
    """
    Process generating rst files.
    This function must be called at initialization of Sphinx's building
    process.

    Parameters
    ----------
    app : Sphinx
        Sphinx Buider.

    Raises
    ------
    ValueError
        Kind of item not found in the package template library.

    Notes
    -----
    
    """

    # get files in the source directory
    genfiles = app.config.doxysummary_generate

    if genfiles is True:
        env = app.builder.env
        genfiles = [env.doc2path(x, base=None) for x in env.found_docs
                    if os.path.isfile(env.doc2path(x))]
    elif genfiles is False:
        pass
    else:
        ext = list(app.config.source_suffix)
        genfiles = [genfile + (ext[0] if not genfile.endswith(tuple(ext)) else '')
                    for genfile in genfiles]

        for entry in genfiles[:]:
            if not os.path.isfile(os.path.join(app.srcdir, entry)):
                logger.warning(__(f'doxysummary_generate: file not found: {entry}'))
                genfiles.remove(entry)

    suffix = get_rst_suffix(app)

    # find all "doxysummary" directives in genfiles
    doxysummary_re = re.compile(r'^(\s*)\.\.\s+doxysummary::\s*')
    toctree_arg_re = re.compile(r'^\s+:toctree:\s*(.*?)\s*$')
    template_arg_re = re.compile(r'^\s+:template:\s*(.*?)\s*$')
    scope_arg_re = re.compile(r'^\s+:scope:\s*(.*?)\s*$')
    items_arg_re = re.compile(r'^\s+(~?[_a-zA-Z][^#"]*)\s*.*?')

    doxysummaries: List[DoxySummaryEntry] = []
    for filename in genfiles:
        filename = os.path.join(app.env.srcdir, filename)
        with open(filename, 'r') as f:
            # initialization of variables
            in_doxysummary = False
            base_indent = ''
            doxysummary_args = {'filename': filename}

            # loop over all lines in file
            lines = f.read().splitlines()
            for line in lines:

                if in_doxysummary:
                    m = toctree_arg_re.match(line)  # read ":toctree:"
                    if m:
                        doxysummary_args['toctree'] = m.group(1)
                        continue

                    m = template_arg_re.match(line)  # read ":template:"
                    if m:
                        doxysummary_args['template'] = m.group(1)
                        continue

                    m = scope_arg_re.match(line)  # read ":scope:"
                    if m:
                        doxysummary_args['scope'] = m.group(1)
                        continue

                    m = items_arg_re.match(line)  # read items
                    if m:
                        name = m.group(1).strip()
                        if name[0] == '~':
                            name = name[1:]
                        doxysummary_args['name'] = ''.join(split_name(name)[1:])
                        doxysummaries.append(DoxySummaryEntry(**doxysummary_args))
                        continue

                    if not line.strip() or line.startswith(base_indent + " "):
                        continue  # skip empty lines

                    # re-initialize variables
                    in_doxysummary = False
                    base_indent = ''
                    doxysummary_args = {'filename': filename}

                m = doxysummary_re.match(line)
                if m:  # if "..doxysummary::" found
                    in_doxysummary = True
                    base_indent = m.group(1)
                    continue

    # generate files based on the template for each doxysummary
    renderer = DoxySummaryRenderer(app)
    for doxysummary in doxysummaries:
        generated_dir = os.path.join(os.path.dirname(doxysummary.filename),
                                       doxysummary.toctree)
        ensuredir(generated_dir)

        # construct dictionary of keys - values for subtituting to the template
        name = doxysummary.name
        fullname = doxysummary.fullname  # note: mute return type
        fullname_without_args = split_name(fullname)[1]
        kind: str = xml_tree[fullname_without_args][0].kind
        keys = {}
        keys['objname'] = fullname
        keys['module'] = "::".join(fullname.split("::")[:-1])
        keys['fullname'] = fullname
        keys['underline'] = len(fullname) * '='
        keys[kind] = True  # in order to use {%if ...%} in Jinja template

        # auto detect template if template name is 'auto'
        template_name = doxysummary.template
        file_content = renderer.render(template_name, keys)

        # mangle fullname -> filename
        file_name = fullname_to_filename(fullname, suffix)
        generated_filename = os.path.join(generated_dir, file_name)
        with open(generated_filename, 'w') as generated_file:
            generated_file.write(file_content)
