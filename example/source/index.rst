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

Example of a function using namespace.

.. doxysummary::
   :toctree: generated

   example::Example
   example::a_function(Example&) "example::a_function(example::Example&)"

Example of aliasing.

.. doxysummary::
   :toctree: generated

   example::a_long_named_function_for_testing_alias "short_name"


Example of function overloading.

.. doxysummary::
   :toctree: generated

   func_overload(void)
   func_overload(int)
   func_overload(long)
   func_overload(int\*)
   func_overload(int\*\*)
   func_overload(double\* const)
   func_overload(const volatile double\*)
   func_overload(double,double)
   func_overload(const double&)
   func_overload(const double*&)
   func_overload(double&&)
   func_overload(int(&)[3])
   func_overload(int(\*)(double))
   func_overload(int example::Example::*)
   func_overload(std::vector<double>&)
   func_overload(std::vector<int[3]>&)
   func_overload(std::initializer_list<int>)

.. note::

    - Avoid spaces for long declaration. Otherwise, a linebreak may be inserted automatically.
    - Pointers ``*`` must be protected with a backslash ``\*``, e.g. ``f(int*)`` must be declared
      as ``f(int\*)``.
    - ``noexcept``, pre/post condition assertions specifier must be omitted because it is not part of function overloading
      specifications.
    - If function declaration is ``f(void)``, directive argument can be either ``f()`` or
      ``f(void)``. However, if the declaration is ``f()``, RST directive must be ``f()``.

