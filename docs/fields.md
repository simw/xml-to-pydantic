# Fields

## Aliases

When relying on the inferred schema, it is possible to
alter the mapping from python field name to HTML / XML document
tag, by using the alias_generator.

The alias_generator takes in the python field name and outputs
the HTML / XML document tag.

```py
from xml_to_pydantic import ConfigDict, DocModel

xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <element-1>4.53</element-1>
    <element-2>hello</element-2>
</root>
"""


class MyModel(DocModel):
    model_config = ConfigDict(xpath_generator=lambda x: x.replace("_", "-"))
    element_1: float
    element_2: str


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> element_1=4.53 element_2='hello'
```

If all fields are defined using XPath directly on DocField, then
the alias_generator has no effect.

## Unions

```py
from typing import Union

from xml_to_pydantic import DocModel

xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
  <subject>
    <element2>value1</element2>
  </subject>
</root>
"""


class Element1(DocModel):
    element1: str


class Element2(DocModel):
    element2: str


class MyModel(DocModel):
    subject: Union[Element1, Element2]


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> subject=Element2(element2='value1')
```