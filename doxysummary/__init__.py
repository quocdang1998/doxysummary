#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 21:29:53 2022
@author: quocdang
"""

import os
import re
import posixpath
import shlex

from pathlib import Path

from typing import Any, Dict, List, Tuple

from jinja2 import TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.nodes import Node
from docutils.statemachine import StringList

import sphinx
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.locale import __
from sphinx.util import logging, rst
from sphinx.util.docutils import SphinxDirective, switch_source_input
from sphinx.util.osutil import ensuredir
from sphinx.util.template import SphinxTemplateLoader
from sphinx.util.typing import OptionSpec
from sphinx.ext.autodoc.directive import DocumenterBridge, Options
from sphinx.ext.autosummary import autosummary_toc_visit_html,\
                                   autosummary_table_visit_html,\
                                   autosummary_noop,\
                                   autosummary_toc, autosummary_table,\
                                   get_rst_suffix
from sphinx.ext.autosummary.generate import AutosummaryRenderer, _underline

from xml.dom.minidom import parse
from lxml import etree


# =============================================================================
# Step 1: At the beginning of building the doc
# Automatically generate rst files based on the template
# These files must be generated at the beginning of Sphinx
# Or else toctree will unable to find these files
# =============================================================================


class DoxygenItem:

    def __init__(self, refid: str, name: str, kind: str):
        # basic attributes
        self.name = name
        self.kind = kind
        self.refid = refid

        # initialize default attributes
        self.summary = ''
        self.args: List[Tuple[str, str]] = None
        self.return_type: str = ''
        self.overloaded: bool = False

        # append name to all_functions to set overload property
        if self.kind == 'function':
            # firstly appear
            if self.name not in DoxySummary.all_functions.keys():
                DoxySummary.all_functions[self.name] = self
            else:
                DoxySummary.all_functions[self.name].overloaded = True
                self.overloaded = True

    def __repr__(self):
        return f'{self.name:<30s} {self.kind:<10s} {self.summary}'

    def __hash__(self):
        return self.refid

    def set_summary(self, summary: str):
        self.summary = summary

    @property
    def has_summary(self):
        return self.summary != ''

    def set_args(self, args: List[Tuple[str, str]]):
        if self.kind != 'function':
            raise ValueError('Cannot set argument for non function type')
        self.args = args

    def set_return_type(self, return_type: str):
        self.return_type = return_type

    def check_args(self, args: str) -> bool:
        args = args[1:-1]  # trim off ()
        args: List[str] = [x.strip() for x in args.split(',')]

        # perform simple heuristic check
        if len(args) != len(self.args):
            return False
        for arg, xml_arg in zip(args, self.args):
            if xml_arg[0] in arg:
                continue
            else:
                return False
        return True

def getFisrtChildByTagName(element: etree._Element, tag: str):
    """
    Search the first child of XML element by tagname.
    Parameters
    ----------
    element : etree._Element
        XML element to search.
    tag : str
        Name of the tag to search.
    Returns
    -------
    result : List[lxml.etree._Element]
        List of first-level children with tagname to search for.
    """
    result: List[etree._Element] = []
    for child in element.getchildren():
        if child.tag == tag:
            result.append(child)
    return result


def process_generate_xmltree(app: Sphinx) -> None:
    """
    Process creating a look-up table for a tree of Doxygen created xml nodes.
    To be executed at initialization of Sphinx.Builder
    Parameters
    ----------
    app : Sphinx
        Sphinx.Builder.
    Raises
    ------
    ValueError
        When behavior of Doxygen created element not as expected.
    """
    for xmldir in app.config.doxygen_xml:
        # retrieve refid from index.xml
        xmldir = os.path.abspath(xmldir)
        index_fname = os.path.join(xmldir, 'index.xml')
        index_file = parse(index_fname)
        doxygenindex = index_file.firstChild

        # step1: loop over each compound and get its information
        # dict of refid -> DoxygenItem(name, kind, arguments if kind==fucntion)
        index_data: Dict[str, DoxygenItem] = {}
        for compound in doxygenindex.getElementsByTagName('compound'):
            refid = compound.getAttribute('refid')
            kind = compound.getAttribute('kind')
            if not (refid or kind):
                raise ValueError('Cannot detect the compound')
            name = compound.firstChild
            if name.tagName != 'name':
                raise ValueError('Expected first child of "compound" '
                                 'tagged "name"')
            name = name.firstChild.data
            index_data[refid] = DoxygenItem(refid=refid, name=name, kind=kind)

            compound_kind = kind
            for member in compound.getElementsByTagName("member"):
                refid = member.getAttribute('refid')
                kind = member.getAttribute('kind')
                membername = member.firstChild.firstChild.data
                # if compound is not a file, add scope name to member name
                if compound_kind != 'file':
                    membername = "::".join([name, membername])
                index_data[refid] = DoxygenItem(refid=refid, name=membername, kind=kind)

        # step2: find short description and arguments of each refid in all other xml
        for xml_fname in Path(xmldir).rglob('*.xml'):
            xml_file = etree.parse(str(xml_fname))
            for refid in index_data.keys():
                # step2.1: get definition node of item (class/enum/function)
                itemdef = xml_file.xpath(f'''.//*[@id='{refid}']''')
                if itemdef:  # found id
                    itemdef = itemdef[0]  # list of 1 element to element
                    # get brief description
                    brief = getFisrtChildByTagName(itemdef, 'briefdescription')[0]
                    paragraph = brief.getchildren()
                    if paragraph:
                        summary = brief.getchildren()[0].xpath("string()")
                        summary = summary.strip().splitlines()[0]
                    else:
                        summary = ''
                    # in case of empty brief, use detailed instead
                    if summary == '':  # empty brief description
                        # get first paragraph of detailed description if empty
                        detail = getFisrtChildByTagName(itemdef,
                                                        'detaileddescription')[0]
                        paragraph = detail.getchildren()
                        if paragraph:
                            summary = paragraph[0].xpath("string()")
                            summary = summary.strip().splitlines()[0]
                        else:
                            summary = ''
                    index_data[refid].set_summary(summary)

                    # step2.2: get argument and return type if kind is 'function'
                    if index_data[refid].kind == 'function':
                        params = getFisrtChildByTagName(itemdef, 'param')
                        arguments: List[Tuple[str, str]] = []  # args of func
                        if len(params) == 0:  # empty argument list
                            continue
                        for param in params:
                            argtype = param.xpath('.//type')[0].text
                            argname = param.xpath('.//declname')
                            if argname:  # argname is not empty
                                argname = argname[0].text
                            else:  # declare function prototype only
                                argname = ''
                            arguments.append((argtype, argname))
                        index_data[refid].set_args(arguments)

                        return_type = getFisrtChildByTagName(itemdef, 'type')
                        return_type = return_type[0].xpath("string()")
                        index_data[refid].set_return_type(return_type)

        # step3: integrate all items to the class-bound variable DoxySummary.summaries
        for refid in index_data.keys():
            # deprecated
            #DoxySummary.kinds[index_data[refid].name] = index_data[refid].kind
            #DoxySummary.summaries[index_data[refid].name] = index_data[refid].summary

            # official
            if index_data[refid].name not in DoxySummary.xmltree.keys():
                DoxySummary.xmltree[index_data[refid].name] = [index_data[refid]]
            else:
                DoxySummary.xmltree[index_data[refid].name].append(index_data[refid])


def funcname_only(name: str):
    name_without_args = name.split('(')[0].strip()
    has_args = '(' in name and ')' in name
    if has_args:
        args = '(' + name.split('(')[1]
    else:
        args = ''
    tokens = name_without_args.split()
    if len(tokens) == 1:
        funcname = tokens[0]
    else:
        funcname = tokens[1]
    return funcname


def del_restype(name: str):
    name_without_args = name.split('(')[0].strip()
    has_args = '(' in name and ')' in name
    if has_args:
        args = '(' + name.split('(')[1]
    else:
        args = ''
    tokens = name_without_args.split()
    if len(tokens) == 1:
        funcname = tokens[0]
    else:
        funcname = tokens[1]
    return funcname + args


def add_scope_to_name(name: str, scope: str):
    name_without_args = name.split('(')[0].strip()
    has_args = '(' in name and ')' in name
    if has_args:
        args = '(' + name.split('(')[1]
    else:
        args = ''
    tokens = name_without_args.split()
    if len(tokens) == 1:
        restype = ''
        funcname = tokens[0]
    else:
        restype = tokens[0] + ' '
        funcname = tokens[1]
    funcname = '::'.join([scope, funcname])
    return restype + funcname + args


class DoxySummaryEntry:

    def __init__(self, filename: str, name: str,
                 template: str= 'cppbase.rst', toctree: str = '',
                 scope: str = ''):
        """
        Simple class representing an entry in \"doxysummary\" directive.
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
        Returns
        -------
        str
            Fullname of the entry.
        """
        if self.scope == '':
            return self.name
        else:
            return add_scope_to_name(self.name, self.scope)

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
        Returns
        -------
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


logger = logging.getLogger(__name__)


def fullname_to_filename (item_name: str, suffix: str):
    """
    Convert item fullname to filename).
    
    Parameters
    ----------
    item_name : str
        Full name of item in C++ code (can be declaration or prototype).
    suffix: str
        File suffix.
    Returns
    -------
    str
        Name of the file.
    """
    file_name = item_name
    file_name = file_name.replace('::', '.')  # avoid ':' in scope
    file_name = file_name.replace('(', '6')  # avoid '('
    file_name = file_name.replace(')', '9')  # avoid ')'
    file_name = file_name.replace('<', '4')  # avoid '<'
    file_name = file_name.replace('>', '7')  # avoid '>'
    file_name = file_name.replace('&', '_amp_')  # avoid '&'
    file_name = file_name.replace(' ', '-')  # avoid '&'

    return file_name + suffix


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
    """

    # get files in the source directory
    genfiles = app.config.autosummary_generate

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
                        doxysummary_args['name'] = del_restype(name)
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
    renderer = AutosummaryRenderer(app)
    for doxysummary in doxysummaries:
        generated_dir = posixpath.join(posixpath.dirname(doxysummary.filename),
                                       doxysummary.toctree)
        ensuredir(generated_dir)

        # construct dictionary of keys - values for subtituting to the template
        name = doxysummary.name
        fullname = doxysummary.fullname
        fullname_without_args = fullname.split('(')[0]
        kind: str = DoxySummary.xmltree[fullname_without_args][0].kind
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
        generated_filename = posixpath.join(generated_dir, file_name)
        with open(generated_filename, 'w') as generated_file:
            generated_file.write(file_content)


# =============================================================================
# Step 2 : read directive at parsing time
# Directive = reStructuredText directive
# Instruct Sphinx how to read the customized directive "doxysummary"
# =============================================================================


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
    #: dictionary of all fristly found DoxygenItem of type functions
    all_functions: Dict[str, DoxygenItem] = {}
    #: xmltree to all items
    xmltree: Dict[str, List[DoxygenItem]] = {}

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
        Returns
        -------
        List[docutils.nodes.Node]
            List of docutils nodes to be added to the document.
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
                    name = add_scope_to_name(name, self.options['scope'].strip())
                names.append(del_restype(name))

                # append displayname if alias detected -> overwrite effect of ~
                m = re.search(alias_regex, x.strip())
                if m:
                    ignore_parent = False
                    alias = m.group(0)
                    alias_count = len(shlex.split(alias))
                    if alias_count > 1:
                        raise ValueError(f'Expected 1 alias, got '
                                         f'{alias_count}.')
                    if alias_count == 1:
                        displaynames.append(shlex.split(alias)[0])
                # if alias not detected, display in-scope name
                elif ignore_parent:
                    displaynames.append(name.split("::")[-1])  # attention !
                else:
                    displaynames.append(name)

        # get summary
        descs: Dict[str, str] = {}
        restype: Dict[str, str] = {}
        for name in names:
            items_list: List[DoxygenItem] = DoxySummary.xmltree[funcname_only(name)]
            func_args = re.search('\(.*\)', name)
            if func_args:  # if name is a function with arguments
                func_args = func_args.group(0)
                for item in items_list:  # loop over functions with the same name
                    if item.check_args(func_args):  # found a matched definition
                        descs[name] = item.summary
                        restype[name] = item.return_type
                        break
                if name not in descs.keys():
                    raise ValueError('Function not found, '
                                     'please enter the correct C++ declaration/prototype.')
            else:
                descs[name] = DoxySummary.xmltree[name][0].summary

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
            if DoxySummary.xmltree[funcname_only(name)][0].kind == 'define':
                qualifier = 'c:macro'
            if len(DoxySummary.xmltree[funcname_only(name)]) > 1:
                qualifier = 'cpp:func'
                linkname = restype[name] + ' ' + name
            else:
                linkname = name
            col1 = ':%s:`%s <%s>`' % (qualifier, displayname, linkname)
            desc = descs[name]
            append_row(col1, desc)

        # add a hidden toctree and create files
        dirname = posixpath.dirname(self.env.docname)
        if 'toctree' in self.options:
            tree_prefix = self.options['toctree'].strip()
        else:
            tree_prefix = ''

        docnames: List[str] = []  # list of entries of hidden toctree
        for name in names:
            file_name = fullname_to_filename(del_restype(name), '')
            docname = posixpath.join(tree_prefix, file_name)
            docname = posixpath.normpath(posixpath.join(dirname, docname))
            docnames.append(docname)

        if docnames:
            tocnode = addnodes.toctree()
            tocnode['includefiles'] = docnames
            tocnode['entries'] = [(None, docn) for docn in docnames]
            tocnode['hidden'] = True
            tocnode['glob'] = None

        return [table_spec, table, tocnode]


# =============================================================================
# Step 3 : register 2 classes nodes for doxysummary table and toctree
# =============================================================================


class doxysummary_toc(autosummary_toc):
    pass


class doxysummary_table(autosummary_table):
    pass


# adding all elements to Sphinx application
def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension('breathe')
    app.add_node(doxysummary_toc,
                 html=(autosummary_toc_visit_html, autosummary_noop),
                 latex=(autosummary_noop, autosummary_noop),
                 text=(autosummary_noop, autosummary_noop),
                 man=(autosummary_noop, autosummary_noop),
                 texinfo=(autosummary_noop, autosummary_noop))
    app.add_node(doxysummary_table,
                 html=(autosummary_table_visit_html, autosummary_noop),
                 latex=(autosummary_noop, autosummary_noop),
                 text=(autosummary_noop, autosummary_noop),
                 man=(autosummary_noop, autosummary_noop),
                 texinfo=(autosummary_noop, autosummary_noop))

    app.add_directive('doxysummary', DoxySummary)
    # app.add_role('autolink', AutoLink())
    app.connect('builder-inited', process_generate_xmltree)
    app.connect('builder-inited', process_generate_files)

    app.add_config_value(name='doxygen_xml', default=[os.path.abspath('./xml')],
                         rebuild=True, types=[list])

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}

