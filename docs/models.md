# Models

## Model Usage

In xml-to-pydantic, the mapping from HTML / XML to Python object
fields is through `DocModel`.

This is very similar to BaseModel from Pydantic (in fact, it extends it),
and how it extracts data from JSON or Python dictionaries.

The field extraction is defined through XPath. The XPath can
either be inferred from the structure of the model (if the HTML / XML
structure is simple). Here, this is applied to an HTML document.

```py
from xml_to_pydantic import ConfigDict, DocModel

html_bytes = b"""
<!doctype html>
<html lang="en-US">
  <head>
    <meta charset="utf-8" />
    <title>My page title</title>
  </head>

  <body>
    <header>
      <h1>Header</h1>
    </header>

    <main>
      <p>Paragraph1</p>
      <p>Paragraph2</p>
      <p>Paragraph3</p>
    </main>
  </body>
</html>
"""


class MainContent(DocModel):
    model_config = ConfigDict(xpath_root="/html/body/main")
    p: list[str]


result = MainContent.model_validate_html(html_bytes)
print(result)
#> p=['Paragraph1', 'Paragraph2', 'Paragraph3']
```

Alternatively, explicit XPath can be declared
for each field, here applied to an XML document.

```py
from xml_to_pydantic import DocModel, DocField

xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <element>4.53</element>
    <a href="https://example.com">Link</a>
</root>
"""


class MyModel(DocModel):
    number: float = DocField(xpath="./element/text()")
    href: str = DocField(xpath="./a/@href")


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> number=4.53 href='https://example.com'

assert model.model_fields_set == {"number", "href"}
assert model.model_dump() == {"number": 4.53, "href": "https://example.com"}
```

The resulting Model is also a Pydantic model, and the
instance of the model has all the usual Pydantic methods
and properties (as described in the [Pydantic docs](https://docs.pydantic.dev/latest/concepts/models/#model-methods-and-properties))


## Inferred Schema



## Nested Models

```py
from xml_to_pydantic import DocModel, DocField

xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <element1>4.53</element1>
    <element2>
      <a href="https://example.com">Link 1</a>
      <a href="https://example2.com">Linke 2</a>
    </element2>
</root>
"""


class Element2(DocModel):
    href: list[str] = DocField(xpath="./a/@href")


class MyModel(DocModel):
    number: float = DocField(xpath="./element1/text()")
    element2: Element2


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> number=4.53 element2=Element2(href=['https://example.com', 'https://example2.com'])

assert model.model_fields_set == {"number", "element2"}
assert model.model_dump() == {
    "number": 4.53,
    "element2": {
        "href": ['https://example.com', 'https://example2.com']
    },
}
```