#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 14:42:36 2022

@author: quocdang
"""

import os
import platform
import re
import shlex

from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.nodes import Node
from docutils.statemachine import StringList

from sphinx import addnodes
from sphinx.ext.autodoc.directive import DocumenterBridge, Options
from sphinx.ext.autosummary import autosummary_table
from sphinx.util.docutils import SphinxDirective, switch_source_input
from sphinx.util.typing import OptionSpec

from sphinx_doxysummary.xmltree import xml_tree, DoxygenItem
from sphinx_doxysummary.utils import split_name, fullname_to_filename

class DoxySummary(SphinxDirective):
    """
    Class represents the directive ``doxysummary`` when Sphinx parses inputs.
    """

    # Additional attributes
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    #: Dictionary of options of the directive.
    option_spec: OptionSpec = {
        'toctree': directives.unchanged,  # where to generate files
        'template': directives.unchanged_required,  # name of template
        'scope': directives.unchanged,  # scoped item (namespace, class, enum)
    }

    def run(self) -> List[Node]:
        """
        Method called after Sphinx has read the directive ``doxysummary``.

        It retrieves the full name of each entry, creates a summary table with
        alias and brief description from Doxygen created XML files, and builds
        a hidden toctree linking to the generated files at the beginning of
        Sphinx build process.

        Raises
        ------
        ValueError
            When a line having more than 1 alias.

        Return
        ------
        List[docutils.nodes.Node]
            List of docutils nodes to be added to the document.

        Notes
        -----
        The ``name`` variable in the method ``run`` represents the full scoped
        name without return type and with arguments.
        """
        # create documenter bridge
        self.bridge = DocumenterBridge(self.env, self.state.document.reporter,
                                       Options(), self.lineno, self.state)

        # get input by lines
        names: List[str] = []
        displaynames: List[str] = []  # name to be displayed to the table
        item_regex = r'^(~?[_a-zA-Z][^#"]*)\s*.*?'
        alias_regex = r'".+"'
        for x in self.content:
            # if not empty line
            if x.strip() and re.search(r'^[~a-zA-Z_]', x.strip()[0]):
                name = re.search(item_regex, x).group(1).strip()

                # check if name starts with a ~
                ignore_parent: bool = False
                if name[0] == '~':
                    ignore_parent = True
                    name = name[1:]  # remove tilde

                # retrieve the fullname
                if 'scope' in self.options:
                    splitted = split_name(name)[1:]
                    splitted[0] = '::'.join([self.options['scope'].strip(), splitted[0]])
                    name = ''.join(splitted)
                # delete return type
                name = ''.join(split_name(name)[1:])
                names.append(name)

                # append displayname if alias detected -> overwrite effect of ~
                m = re.search(alias_regex, x.strip())
                if m:
                    ignore_parent = False
                    alias = m.group(0).strip('"')
                    displaynames.append(alias)
                # if alias not detected, display in-scope name
                elif ignore_parent:
                    displaynames.append(name.split("::")[-1])  # attention !
                else:
                    displaynames.append(name)

        # get summary
        descs: Dict[str, str] = {}
        restype: Dict[str, str] = {}
        for name in names:
            items_list: List[DoxygenItem] = xml_tree[split_name(name)[1]]
            func_args = split_name(name)[-1]
            if func_args:  # if name is a function with arguments
                for item in items_list:  # loop over functions with the same name
                    if item.check_args(func_args):  # found a matched definition
                        descs[name] = item.summary
                        restype[name] = item.return_type
                        break
                if name not in descs.keys():
                    raise ValueError('Function not found, '
                                     'please enter the correct C++ declaration/prototype.')
            else:
                descs[name] = xml_tree[name][0].summary

        # initialize table to be returned
        table_spec = addnodes.tabular_col_spec()
        table_spec['spec'] = r'\X{1}{2}\X{1}{2}'

        table = autosummary_table('')
        real_table = nodes.table('', classes=['longtable'])
        table.append(real_table)
        group = nodes.tgroup('', cols=2)
        real_table.append(group)
        group.append(nodes.colspec('', colwidth=10))
        group.append(nodes.colspec('', colwidth=90))
        body = nodes.tbody('')
        group.append(body)

        def append_row(*column_texts: str) -> None:
            row = nodes.row('')
            source, line = self.state_machine.get_source_and_line()
            for text in column_texts:
                node = nodes.paragraph('')
                vl = StringList()
                vl.append(text, '%s:%d:<autosummary>' % (source, line))
                with switch_source_input(self.state, vl):
                    self.state.nested_parse(vl, 0, node)
                    try:
                        if isinstance(node[0], nodes.paragraph):
                            node = node[0]
                    except IndexError:
                        pass
                    row.append(nodes.entry('', node))
            body.append(row)

        # add each line to table with description
        for name, displayname in zip(names, displaynames):
            qualifier = 'cpp:any'
            # "define" macros is not included in role cpp:any
            if xml_tree[split_name(name)[1]][0].kind == 'define':
                qualifier = 'c:macro'
            if len(xml_tree[split_name(name)[1]]) > 1:
                qualifier = 'cpp:func'
                linkname = restype[name] + ' ' + name
            else:
                linkname = name
            # get description (summary)
            desc = descs[name]
            # if name are template -> add backslash before '<' and '>'
            displayname = displayname.replace('<', '\<').replace('>', '\>')
            name = name.replace('<', '\<').replace('>', '\>')
            col1 = ':%s:`%s <%s>`' % (qualifier, displayname, linkname)
            append_row(col1, desc)

        # add a hidden toctree and create files
        dirname = os.path.dirname(self.env.docname)
        if 'toctree' in self.options:
            tree_prefix = self.options['toctree'].strip()
        else:
            tree_prefix = ''

        docnames: List[str] = []  # list of entries of hidden toctree
        for name in names:
            file_name = fullname_to_filename(name, '')
            docname = os.path.join(tree_prefix, file_name)
            docname = os.path.normpath(os.path.join(dirname, docname))
            if platform.system() == "Windows":
                docname = docname.replace('\\', '/')
            docnames.append(docname)

        if docnames:
            tocnode = addnodes.toctree()
            tocnode['includefiles'] = docnames
            tocnode['entries'] = [(None, docn) for docn in docnames]
            tocnode['hidden'] = True
            tocnode['glob'] = None
            tocnode['maxdepth'] = -1

        return [table_spec, table, tocnode]