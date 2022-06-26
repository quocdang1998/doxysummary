Configuration
=============

DoxySummary provides these following config variables:

:``doxygen_xml`` (mandatory): Paths to Doxygen XML directories. Each directory is a
   project.

:``doxysummary_generate``: Automatically generate rst source files based on
   template. Default: ``True``.



Alias
=====

DoxySummary allows users to replace the display name of an entry in the summary
table through aliasing.

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated

      an_object_with_a_very_long_name "short_name"

.. note::

   Alias should not have any space in between.

.. note::

   Putting a ``~`` before an entry helps removing the scope name. However, this
   feature is overridden by the alias.


Change template
===============

Users can write their own template for generated files with doxysummary
(similar to the option in autosummary).

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated
      :template: mycpp.rst

      Foo

.. warning::

   Recursively auto-generating rst source files is not supported. Having
   directive ``doxysummary`` inside of template file will return error.


Scope
=====

For multiple objects belong to the same scope (like namespace, class, scoped
enum), the option scope can help to shorten the typed name.

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated
      :scope: mynamespace

      MyClass
      my_function
      my_variable

.. note::

   The display name in the summary table is the fullscope name. To display only
   the non-scoped name, use aslias or ``~`` instead.


Function Overloading
====================

C++ allows many functions with different argument types to share the same name.
If a function is overloaded, its argument type (with or without argument name)
must be declared.

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated

      my_function(int)
      my_function(char, char)
      my_function(std::vector<double> &)


