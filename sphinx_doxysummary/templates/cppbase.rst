{{ objname }}
{{ underline }}

{%+ if class -%}
.. doxygenclass:: {{ fullname }}
   :members:
   :protected-members:
   :private-members:
   :undoc-members:
{% endif %}

{%- if struct -%}
.. doxygenstruct:: {{ fullname }}
   :members:
   :protected-members:
   :private-members:
   :undoc-members:
{% endif %}


{%- if function -%}
.. doxygenfunction:: {{ fullname }}
{% endif %}

{%- if enum -%}
.. doxygenenum:: {{ fullname }}
{% endif %}

{%- if enumvalue -%}
.. doxygenenumvalue:: {{ fullname }}
{% endif %}

{%- if variable -%}
.. doxygenvariable:: {{ fullname }}
{% endif %}

{%- if typedef -%}
.. doxygentypedef:: {{ fullname }}
{% endif %}

{%- if define -%}
.. doxygendefine:: {{ fullname }}
{% endif %}

{%- if concept -%}
.. doxygenconcept:: {{ fullname }}
{% endif %}

{%- if union -%}
.. doxygenunion:: {{ fullname }}
{% endif %}
