#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 13:50:43 2022

@author: dn266595
"""

from distutils.core import setup

setup_args = {
    'name': 'sphinx-ext-doxysummary',

    'version': '1.0.0',

    'description': ('Sphinx extension for autosummary with Doxygen entries '
                    'created by the package ``breathe``.'),

    'author': 'Dinh Quoc Dang Nguyen',

    'author_email': 'quocdang1998@gmail.com',

    'packages': ['sphinx.ext.doxysummary'],
    'package_dir': {'sphinx.ext.doxysummary': 'doxysummary'},
    'package_data': {
        'sphinx.ext.doxysummary': ['templates/*.rst']
    },

    'install_requires': ['sphinx', 'breathe'],
    }

setup(**setup_args)