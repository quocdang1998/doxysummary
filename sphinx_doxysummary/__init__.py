#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 21:29:53 2022
@author: quocdang
"""

import os

from typing import Any, Dict, List, Tuple

import sphinx
from sphinx.application import Sphinx

from sphinx_doxysummary.xmltree import process_generate_xmltree
from sphinx_doxysummary.generate import process_generate_files
from sphinx_doxysummary.directive import DoxySummary


# adding all elements to Sphinx application
def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension('sphinx.ext.autosummary')
    app.setup_extension('breathe')

    app.add_directive('doxysummary', DoxySummary)
    # app.add_role('autolink', AutoLink())
    app.connect('builder-inited', process_generate_xmltree)
    app.connect('builder-inited', process_generate_files)

    app.add_config_value(name='doxysummary_generate', default=True,
                         rebuild=True, types=[bool])
    app.add_config_value(name='doxygen_xml', default=[os.path.abspath('./xml')],
                         rebuild=True, types=[list])

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}

