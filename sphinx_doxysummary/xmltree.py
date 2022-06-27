#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 21:36:51 2022

@author: quocdang
"""

import os
from pathlib import Path

from typing import Dict, List, Tuple

from sphinx.application import Sphinx

from xml.dom.minidom import parse
from lxml import etree

from sphinx_doxysummary.utils import getFisrtChildByTagName, compare_type

class DoxygenItem:
    """Item read from Doxygen generated xml.

    Attributes
    ----------
    name: str
        Name of the item.
    kind: str
        Kind of the item.
    refid: str
        Reference ID of the item.
    summary: str
        Brief description of the item.
    args: List[Tuple[str, str]]
        Arguments of a function in the form of a list of pairs (argtype,
        argname).
    return_type: str
        Return type of the function.
    overload: bool
        Wether function is overloaded by another function or not.
    """

    def __init__(self, refid: str, name: str, kind: str):
        """
        Parameters
        ----------
        refid: str
            Reference ID of the item within the xml document.
        name: str
            Name of the item (full scope).
        kind: str
            Kind of the item (one of the following values: class, struct,
            function, variable, enum, enumvalue, typedef, define, namespace,
            file).
        """
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
            global all_functions
            # firstly appear
            if self.name not in all_functions.keys():
                all_functions[self.name] = self
            else:
                all_functions[self.name].overloaded = True
                self.overloaded = True

    def __repr__(self):
        """Output when print this object."""
        return f'{self.name:<30s} {self.kind:<10s} {self.summary}'

    def __hash__(self):
        return self.refid

    def set_summary(self, summary: str):
        """Set summary of the item.

        Parameters
        ----------
        summary: str
            Brief description of the item.
        """
        self.summary = summary

    @property
    def has_summary(self) -> bool:
        """Check if the item has a summary or not."""
        return self.summary != ''

    def set_args(self, args: List[Tuple[str, str]]):
        """Set arguments of the item if the item is a function.

        Parameters
        ----------
        args: List[Tuple[str, str]]
            Arguments of the function.

        Raises
        ------
        ValueError
            When the item is not a function.
        """
        if self.kind != 'function':
            raise ValueError('Cannot set argument for non function type')
        self.args = args

    def set_return_type(self, return_type: str):
        """Set return type of the item if the item is a function.

        Parameters
        ----------
        return_type: str
            Return type of the function.

        Raises
        ------
        ValueError
            When the item is not a function.
        """
        if self.kind != 'function':
            raise ValueError('Cannot set return type for non function type')
        self.return_type = return_type

    def check_args(self, args: str) -> bool:
        """Check if arguments of a prototype / declaration match the arguments
        of the item.

        Parameters
        ----------
        args: str
            Arguments of the prototype / declaration in form of a string and
            enclosed in parentheses.

        Examples
        --------
        >>> d = DoxygenItem(refid, name, kind)
        >>> ...  # set summary, args and return type
        >>> d.check_args('(char a, char b)')
        >>> d.check_args('(double *, int)')
        """
        args = args[1:-1]  # trim off ()
        args: List[str] = [x.strip() for x in args.split(',')]

        # perform simple heuristic check
        if len(args) != len(self.args):
            return False
        for arg, xml_arg in zip(args, self.args):
            xml_arg_copy = ' '.join(xml_arg)
            if not compare_type(arg, xml_arg_copy):
                return False
        return True


all_functions = {}  # Dict[str, List[DoxygenItem]]
xml_tree = {}  # Dict[str, List[DoxygenItem]]
"""Map of item names to a list of corresponding DoxygenItem objects."""


def process_generate_xmltree(app: Sphinx) -> None:
    """Create a tree of name -> ``DoxygenItem``.

    This process parses through all xml files in all Doxygen projects which are
    declared in the config variable ``doxygen_xml``, and creates a look-up
    table (i.e. a map of item full scope name to its corresponding DexygenItem
    objects) stored in the extern variable ``xml_tree``.

    Parameters
    ----------
    app : Sphinx
        Sphinx.Builder.

    Raises
    ------
    ValueError
        When the behavior of Doxygen-created XML elements are not as expected.

    Notes
    -----
    - This process should be executed at the initialization of the building
      process of Sphinx.

    - The name saved in ``xml_tree`` is the full scope name of item.
    """
    for xmldir in app.config.doxygen_xml:
        # step1: retrieve reference IDs from index.xml of the Doxygen project
        xmldir = os.path.abspath(xmldir)
        index_fname = os.path.join(xmldir, 'index.xml')
        index_file = parse(index_fname)
        doxygenindex = index_file.firstChild

        # step2: loop over each "compound" in index and get its information
        # index_data = dict of refid -> DoxygenItem(name, kind)
        index_data: Dict[str, DoxygenItem] = {}
        for compound in doxygenindex.getElementsByTagName('compound'):
            # step2.1: get the information of the 'compound' node
            refid = compound.getAttribute('refid')
            compound_kind = compound.getAttribute('kind')
            if not (refid or compound_kind):
                raise ValueError('Cannot detect the compound')
            compound_name = compound.firstChild
            if compound_name.tagName != 'name':
                raise ValueError('Expected first child of "compound" '
                                 'tagged "name"')
            compound_name = compound_name.firstChild.data
            index_data[refid] = DoxygenItem(refid=refid, name=compound_name, kind=compound_kind)

            # step2.2: get information of childnode 'member' of 'compound'
            enumname = ''
            for member in compound.getElementsByTagName("member"):
                refid = member.getAttribute('refid')
                member_kind = member.getAttribute('kind')
                member_name = member.firstChild.firstChild.data
                # enumvalue name must be scoped in the enum name
                if compound_kind == 'enum':
                    enumname = member_name
                elif compound_kind == 'enumvalue':
                    member_name = '::'.join([enumname, member_name])
                # if compound is not a file, add scope name to member name
                if compound_kind != 'file':
                    member_name = '::'.join([compound_name, member_name])
                index_data[refid] = DoxygenItem(refid=refid, name=member_name, kind=member_kind)

        # step3: get item summary (first paragraph of the brief description, or
        # first paragraph of the detatiled description if the former choice is
        # empty) and item arguments (if item is function) in all other xml files
        for xml_fname in Path(xmldir).rglob('*.xml'):
            xml_file = etree.parse(str(xml_fname))
            for refid in index_data.keys():
                itemdef = xml_file.xpath(f'''.//*[@id='{refid}']''')
                if itemdef:  # definition node found in the file
                    itemdef = itemdef[0]
                    # step3.1: get item summary
                    # get brief description
                    brief = getFisrtChildByTagName(itemdef, 'briefdescription')[0]
                    paragraph = brief.getchildren()
                    if paragraph:
                        summary = brief.getchildren()[0].xpath("string()")
                        summary = summary.strip().splitlines()[0]
                    else:
                        summary = ''
                    # in case of an empty brief descrip[tion, use detailed
                    # description instead
                    if summary == '':
                        detail = getFisrtChildByTagName(itemdef, 'detaileddescription')[0]
                        paragraph = detail.getchildren()
                        if paragraph:
                            summary = paragraph[0].xpath("string()")
                            summary = summary.strip().splitlines()[0]
                        else:
                            summary = ''
                    index_data[refid].set_summary(summary)

                    # step3.2: get argument and return type if kind is 'function'
                    if index_data[refid].kind == 'function':
                        params = getFisrtChildByTagName(itemdef, 'param')
                        arguments: List[Tuple[str, str]] = []  # args of func
                        if len(params) == 0:  # empty argument list
                            index_data[refid].set_args([('void', '')])
                            continue
                        # get argtype and argname
                        for param in params:
                            argtype = param.xpath('.//type')[0].xpath("string()")
                            argname = param.xpath('.//declname')
                            if argname:  # argname is not empty
                                argname = argname[0].text
                            else:  # declare function prototype only
                                argname = ''
                            arguments.append((argtype, argname))
                        index_data[refid].set_args(arguments)
                        # get return type
                        return_type = getFisrtChildByTagName(itemdef, 'type')
                        return_type = return_type[0].xpath("string()")
                        index_data[refid].set_return_type(return_type)

        # step4: integrate all items to the global variable xmltree
        global xml_tree
        for refid in index_data.keys():
            if index_data[refid].name not in xml_tree.keys():
                xml_tree[index_data[refid].name] = [index_data[refid]]
            else:
                xml_tree[index_data[refid].name].append(index_data[refid])
