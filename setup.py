#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 13:50:43 2022

@author: dn266595

Future implementation: set_verbosity for debugging, mute auto generate and
'set alias as page title'
"""

from distutils.core import setup

setup_args = {
    'name': 'sphinx-doxysummary',

    'version': '2.2.1',

    'description': ('Sphinx extension for autosummary with Doxygen entries '
                    'created by the package ``breathe``.'),

    'author': 'Dinh Quoc Dang Nguyen',

    'author_email': 'quocdang1998@gmail.com',

    'packages': ['sphinx_doxysummary'],
    'package_dir': {'sphinx_doxysummary': 'sphinx_doxysummary'},
    'package_data': {
        'sphinx-doxysummary.templates': ['*.rst']
    },

    'install_requires': ['sphinx', 'breathe', 'lxml'],
    'extras_require': {'example': 'sphinx-rtd-theme'},
}

setup(**setup_args)
