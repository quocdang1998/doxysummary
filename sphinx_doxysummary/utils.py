#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 21:36:51 2022

@author: quocdang
"""

import re

from typing import Any, Dict, List, Tuple, Set

from lxml import etree

keywords = [
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor',
    'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t',
    'class', 'compl', 'concept', 'const', 'consteval', 'constexpr', 'constinit',
    'const_cast', 'continue',
    'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast', 'else',
    'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend',
    'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new',
    'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq',
    'private', 'protected', 'public', 'register', 'reinterpret_cast',
    'requires', 'return', 'short', 'signed', 'sizeof', 'static',
    'static_assert', 'static_cast', 'struct', 'switch', 'template', 'this',
    'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid', 'typename',
    'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'wchar_t',
    'while', 'xor', 'xor_eq',
]

def tokenize_arg(argument: str) -> List[Set[str]]:
    """Split a C++ argument into its components.
    
    Parameters
    ----------
    argument: str
        One argument of the function.
    
    Return
    ------
    List[Set[str]]
        List of set of tokens from the argument.

    Examples
    --------
    >>> tokenize_arg('int argc')  # type + var-name
    [{'argc', 'int'}]
    >>> tokenize_arg('const char *a')  # with specifier
    [{'char'}, {'*'}, {'a'}]
    >>> tokenize_arg('char&& a')  # reference to r-value
    [{'char'}, {'&'}, {'&'}, {'a'}]
    >>> tokenize_arg('const std::vector< double *, int > & x_')  # template
    [{'const', 'std::vector<double *, int>'}, {'&'}, {'x_'}]
    """
    # step1: preprocessing
    # remove default argument value
    arg = argument.rsplit('=', maxsplit=1)[0]
    # remove space around scope(::) and template operator(<>)
    arg = ''.join([temp.strip() for temp in re.split('([:<>][:]*)', arg)])
    # step2: split
    # split by special character (not a character, digit, space, ':' or '<''>')
    # if that character is not in between '<' and '>'
    tokens = re.split('([^\w\s\d_:<>])(?![^<]*\>)', arg)
    result = []
    for t in tokens:  # for each permutable group -> convert to set
        if not t.strip():  # skip empty token
            continue
        t = re.split('[\s](?![^<]*\>)', t.strip())
        t = set([temp for temp in t if temp != ''])
        result.append(t)
    if result == []:  #empty argument -> void
        result = [{'void'}]
    return result


def compare_type(arg1: str, arg2: str) -> bool:
    """Check if type of 2 arguments are the same.
    
    Parameters
    ----------
    arg1: str
        First argument.
    arg2: str
        Second argument.
    
    Return
    ------
    bool
        True if 2 arguments have the same type.
    
    Examples
    --------
    >>> compare_type('const int a', 'int const')  # normal case
    True
    >>> compare_type('const int * a', 'int *')  # without specifier
    False
    >>> compare_type('const int &', 'int const &')  # change specifier position
    True
    >>> compare_type('std::vector<const double *> &', 'std::vector<double const> &')  # template
    False
    >>> compare_type('void', '')
    True
    """
    tokens1 = tokenize_arg(arg1)
    tokens2 = tokenize_arg(arg2)

    # special treatment for the last token, because it may hold argname
    # if length of 2 tokens are too far apart --> False
    if abs(len(tokens1) - len(tokens2)) > 1:
        return False
    if len(tokens1) != len(tokens2):  # differ by 1 token (argument name)
        # find the last args token
        if len(tokens1) < len(tokens2):
            last_arg = tokens2[-1]
        else:
            last_arg = tokens1[-1]
        # if differ more than 1 item -> False
        if len(last_arg) > 1:
            return False
        else:
            last_arg = last_arg.pop()
            # check if last_arg obey variable name rule
            if last_arg in keywords or not re.match('^[\w_][\w\d_]*', last_arg):
                return False

    min_num = min(len(tokens1), len(tokens2))
    for i in range(min_num):
        if tokens1[i] == tokens2[i]:
            continue
        # if 2 tokens are different
        #1. check if argname in the last item
        if i == min_num-1:
            if tokens1[i] - tokens2[i]:
                diff_from_token1 = True
                difference = tokens1[i] - tokens2[i]
            else:
                diff_from_token1 = False
                difference = tokens2[i] - tokens1[i]
            if len(difference) == 1:
                last_arg = difference.pop()
                if last_arg in keywords or not re.match('^[\w_][\w\d_]*', last_arg):
                    return False
                else:
                    if diff_from_token1:
                        tokens1[i].remove(last_arg)
                    else:
                        tokens2[i].remove(last_arg)
        #2. tokenize template and compare
        token1 = sorted(tokens1[i])
        token2 = sorted(tokens2[i])
        if len(token1) != len(token2):
            return False
        for t1, t2 in zip(token1, token2):
            if t1 == t2:
                continue
            elif '<' in t1 and '>' in t1 and '<' in t2 and '>' in t2:
                before1, _1 = t1.split('<', maxsplit=1)
                template1, after1 = _1.rsplit('>', maxsplit=1)
                template1 = [t.strip() for t in template1.split(',')]
                before2, _2 = t2.split('<', maxsplit=1)
                template2, after2 = _2.rsplit('>', maxsplit=1)
                template2 = [t.strip() for t in template2.split(',')]

                if before1 != before2 or after1 != after2:
                    return False
                if len(template1) != len(template2):
                    return False
                for tparam1, tparam2 in zip(template1, template2):
                    if not compare_type(tparam1, tparam2):
                        return False
            else:
                return False
    return True


def getFisrtChildByTagName(element: etree._Element, tag: str) -> List[etree._Element]:
    """Search the first child of XML element by tagname.

    Parameters
    ----------
    element : etree._Element
        XML element to search.
    tag : str
        Name of the tag to search.

    Return
    ------
    result : List[lxml.etree._Element]
        List of first-level children with tagname to search for.
    """
    result: List[etree._Element] = []
    for child in element.getchildren():
        if child.tag == tag:
            result.append(child)
    return result


def split_name(name: str) -> List[str]:
    """
    Split any item declaration into a list of return type, item name and
    arguments.

    Parameters
    ----------
    name: str
        Declarartion of the item.

    Return
    ------
    List[str]
        List of return type - item name - arguments
    
    Examples
    --------
    >>> split_name('spam::Shrub')
    ['', 'spam::Shrub', '']
    >>> split_name('void hello::hello_world(int a, const std::vector<int> & b)')
    ['void', 'hello::hello_world', '(int a, const std::vector<int> & b)']
    >>> split_name('int * get(int * array)')
    ['int *', 'get', '(int * array)']
    >>> split_name('spam::Spam operator * (spam::Spam & x, spam::Spam & y)')
    ['spam::Spam', 'operator *', '(spam::Spam & x, spam::Spam & y)']
    >>> split_name('void* spam::Spam::operator ->* ()')
    ['void *', 'spam::Spam::operator ->*', '()']
    """
    # remove spaces around ':', '(' and ')'
    name = re.split('([:()])', name)
    name = ''.join([n.strip() for n in name if n .split()])

    # split restype-funcname from args
    name_split_args = re.split('(?<!operator)(\()', name)
    has_args = (len(name_split_args) > 1)
    if has_args:
        args = ''.join(name_split_args[1:])
    else:
        args = ''
    name_without_args = name_split_args[0]

    # split restype from funcname
    o = name_without_args.find('operator')
    if o != -1:
        func_name = name_without_args[o:].replace(' ', '')
        name_without_args = name_without_args[:o]
    else:
        func_name = ''
    tokens = [t for t in re.split('([\s*&])', name_without_args) if t != '']
    if re.match('^[\w_:][\w\d_:]*', tokens[-1]):  # match function name
        func_name = tokens[-1] + func_name
        restype = ' '.join([t.strip() for t in tokens[:-1] if t.strip()])
    else:
        restype = ' '.join([t.strip() for t in tokens[:-1] if t.strip()])
        if func_name == '':
            raise ValueError('Missing function name.')
    return [restype, func_name, args]


def fullname_to_filename(item_name: str, suffix: str):
    """
    Convert special characters in item fullname to valid filename characters.

    Parameters
    ----------
    item_name : str
        Full name of item in C++ code (can be declaration or prototype).
    suffix: str
        File suffix.

    Return
    ------
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

