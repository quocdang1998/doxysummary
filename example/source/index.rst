.. DoxySummary Example documentation master file, created by
   sphinx-quickstart on Sat Jun 25 05:59:12 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DoxySummary Example's documentation!
===============================================

.. raw:: latex

   \setcounter{codelanguage}{1}

Example on a function, class and enum (enumvalue are not available).

.. doxysummary::
   :toctree: generated

   foo_function # anything after the number sign character is a line comment
   Foo
   Spam

Example on a macro (define), typedef, union and struct.

.. doxysummary::
   :toctree: generated

   PI
   real
   UnionExample
   AStruct

Example on a template function and template class.

.. doxysummary::
   :toctree: generated

   template_func
   TemplateClass

Example of concept (from C++20).

.. doxysummary::
   :toctree: generated

   Incrementable

Example of a variable and a function inside a namespace.

.. doxysummary::
   :toctree: generated
   :scope: example

   scoped_variable
   scoped_function

Example of aliasing.

.. doxysummary::
   :toctree: generated

   example::a_long_named_function_for_testing_alias "short_name"


Example of function overloading

.. doxysummary::
   :toctree: generated

   func_overload(void) "func_overload_void"
   func_overload(int) "func_overload_int"
   func_overload(double,double) "func_overload_double_double"
   func_overload(const double &) "func_overload_const_double_&"
   func_overload(double &&) "func_overload_double_&&"
   func_overload(std::vector<double> &) "func_overload_std::vector<double>_&"


