[![Language](https://img.shields.io/badge/language-Python%3E%3D3.6-0076fc)](https://www.python.org/)
[![Package](https://img.shields.io/badge/package-Sphinx-9cf)](https://www.sphinx-doc.org/en/master/)
[![Package](https://img.shields.io/badge/package-Doxygen-9cf)](https://doxygen.nl/)

[![Licence](https://img.shields.io/badge/licence-MIT-blue)](https://github.com/quocdang1998/doxysummary/blob/master/LICENCE)
[![HTML](https://img.shields.io/badge/html-ReadTheDocs-blue)](https://doxysummary.readthedocs.io/en/latest/)
[![PDF](https://img.shields.io/badge/pdf-ReadTheDocs-blue)](https://doxysummary.readthedocs.io/_/downloads/en/latest/pdf/)

Doxysummary
===========

A Sphinx extension for creating autosummary with entries from xml files
generated by Doxygen.


Installation
------------

To install doxysummary:

```console
$ pip install .
```

To build examples:

```console
$ cd example
$ doxygen Doxyfile
$ make html
```

To compile the doc:

```console
$ cd docs
$ make html
```

Usage
-----

In `conf.py`, add `sphinx_doxysummary` to the list of extensions, and set the
config variable `doxygen_xml` to the list of locations of xml files:

```Python
extensions = [...
    'sphinx_doxysummary',
    ...
]

doxygen_xml = ['./xml']  # each directory corresponds to one Doxygen project
```

Then in the input rst file, add the following directive:

```reStructuredText
.. doxysummary::
   :toctree: generated
   :template: cppclass.rst

   spam::Foo  # this is comment
   Bar
   ~a_long_name_space::MyClass  # only MyClass appears in the summary table
```

**Note**:
- Anything placed after `#` is line comment.
- Display non-scoped name in the summary table by placing a `~` at the
  beginning of the entry

Options
-------

- `:template:` (optional) : name of the template.

- `:toctree:` (optional) : directory in which rst files are generated.

- `:scope:` (optional) : current scope (namespace, class, enum, etc) of the
items.

    ```reStructuredText
    .. doxysummary::
       :toctree: generated
       :template: cppclass.rst
       :scope: fruit

       Cherry  # as same as fruit::Cherry
       Orange  # as same as fruit::Orange
    ```

From version 1.2.0, user can customize the displayed name of the item in the
autosummary table with aliasing:
```reStructuredText
.. doxysummary::
   :toctree: generated
   :template: cppclass.rst

   fruit::Cherry "CppCherry"
   fruit::Orange "CppOrange"  # display name is CppOrange and CppCherry
```

**Note**: Alias containing space is not recommended.

New in version 2.2.0: function overloading is officially supported.
```reStructuredText
.. doxysummary::
   :toctree: generated

   func_overload()
   func_overload(int a) "func_overload(int)"
   func_overload(char,char)
   func_overload(std::vector<double>)
