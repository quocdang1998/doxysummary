Generate rst files
==================

The process of auto-generating rst files which is based on the provided
template, is executed after parsing XML data.

Along with
:doc:`process_generate_xmltree <generated/sphinx_doxysummary.xmltree.process_generate_xmltree>`,
this process is called at the beginning of building the documentation (not when
Sphinx is parsing rst source files) to avoid internal linking problems.

.. autosummary::
   :nosignatures:
   :toctree: generated
   :template: pyobject.rst

   ~sphinx_doxysummary.generate.DoxySummaryEntry
   ~sphinx_doxysummary.generate.DoxySummaryRenderer
   ~sphinx_doxysummary.generate.process_generate_files
