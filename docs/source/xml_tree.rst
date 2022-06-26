Generate XML tree
=================

The module ``sphinx_doxysummary.xmltree`` is meant for creating a map from item
names to their corresponding Doxygen descriptions. The result is saved to the
module variable ``xml_tree``, which is called when Sphinx parses rst files, in
order to retrieve the summary of the item with the name given.

Note that because function overloading is allowed in C++, the generated map is
one-to-many: a name is mapped to a list of all possible descriptionw sharing
the same name.

.. autosummary::
   :nosignatures:
   :toctree: generated
   :template: pyobject.rst

   ~sphinx_doxysummary.xmltree.DoxygenItem
   ~sphinx_doxysummary.xmltree.process_generate_xmltree
   ~sphinx_doxysummary.xmltree.xml_tree