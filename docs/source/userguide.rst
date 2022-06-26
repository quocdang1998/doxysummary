Configuration
=============

DoxySummary provides the following config variables:

:``doxygen_xml``: A list of path to Doxygen XML directories. Each directory is
   a project. This variable is mandatory.

:``doxysummary_generate``: Automatically generate rst source files based on
   template. Default value is ``True``.



Alias
=====

DoxySummary allows user to replace the display name of an entry in the summary
table through aliasing.

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated

      an_object_with_a_very_long_name "short_name"

.. note::

   Alias should not have any space in between.

.. note::

   Putting a tilde before an entry help removing the scope name. However, this
   feature is overridden by the alias.


Change template
===============

Users can write their own template for the generated files with doxysummary
(similar to the same option in autosummary).

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated
      :template: mycpp.rst

      Foo

.. warning::

   Recursively auto generating rst source files is not supported. Having
   directive ``doxysummary`` inside of template file will return error.


Scope
=====

For multiple objects belong to the same scope (namespace, class, scoped enum),
the option scope can help to shorten the typed name.

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated
      :scope: mynamespace

      MyClass
      my_function
      my_variable

.. note::

   The display name in the summary table is the fullscope name. To display only
   the non-scoped name, use aslias or tilde instead.


Function Overloading
====================

C++ allows many functions with differents argument types sharing the same name.
If a function is overloaded, the argument type (with or without argument name)
must be declared.

.. code-block:: restructuredtext

   .. doxysummary::
      :toctree: generated

      my_function(int)
      my_function(char, char)
      my_function(std::vector<double> &)


