# xml-to-pydantic

[![CI](https://github.com/simw/xml-to-pydantic/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/simw/xml-to-pydantic/actions/workflows/test.yml)
[![pypi](https://img.shields.io/pypi/v/xml-to-pydantic.svg)](https://pypi.python.org/pypi/xml-to-pydantic)
[![versions](https://img.shields.io/pypi/pyversions/xml-to-pydantic.svg)](https://github.com/simw/xml-to-pydantic)
[![license](https://img.shields.io/github/license/simw/xml-to-pydantic.svg)](https://github.com/simw/xml-to-pydantic/blob/main/LICENSE)

xml-to-pydantic is a library for Python to convert XML or HTML to pydantic
models. This can be used to:

- Parse and validate a scraped HTML page into a python object
- Parse and validate an XML response from an XML-based API
- Parse and validate data stored in XML format

(Please note that this project is not affiliated in any way with the
great team at [pydantic](https://github.com/pydantic/pydantic).)

[pydantic](https://github.com/pydantic/pydantic) is a Python library
for data validation, applying type hints / annotations. It enables
the creation of easy or complex data validation rules for processing
external data. That data usually comes in JSON format or from a Python
dictionary.

But to process and validate HTML or XML into pydantic models would then require
two steps: convert the HTML or XML to a Python dictionary, then convert to
the pydantic model. This libary provides a convenient way to combine those steps.

Note: if you are using this library to parse external, uncontrolled HTML or XML, you should
be aware of possible attack vectors through XML: [https://github.com/tiran/defusedxml].
This library uses lxml under the hood.

## Installation

Use pip, or your favorite Python package manager (pipenv, poetry, pdm, ...):

```bash
pip install xml-to-pydantic
```

## Usage

The HTML or XML data is extracted using XPath. For simple documents, the XPath can be calcualted
from the model:

```py
from xml_to_pydantic import ConfigDict, XmlBaseModel

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

class MainContent(XmlBaseModel):
    model_config = ConfigDict(xpath_root="/html/body/main")
    p: list[str]

result = MainContent.model_validate_html(html_bytes)
print(result)
#> p=['Paragraph1', 'Paragraph2', 'Paragraph3']
```

```py
from xml_to_pydantic import XmlBaseModel


xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <element>4.53</element>
    <element>3.25</element>
</root>
"""


class MyModel(XmlBaseModel):
    element: list[float]


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> element=[4.53, 3.25]
```

However, for more complicated XML, this one-to-one correspondance may not be
convenient, and a better approach is supplying the xpath directly (similar
to how pydantic allows specifying an alias for a field):

```py
from xml_to_pydantic import XmlBaseModel, XmlField


xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <element>4.53</element>
    <a href="https://example.com">Link</a>
</root>
"""


class MyModel(XmlBaseModel):
    number: float = XmlField(xpath="./element/text()")
    href: str = XmlField(xpath="./a/@href")


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> number=4.53 href='https://example.com'
```

The parsing can also deal with nested models and lists:

```py
from xml_to_pydantic import XmlBaseModel, XmlField


xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <level1>
        <level2>value1</level2>
        <level2>value2</level2>
        <level2>value3</level2>
    </level1>
    <level11>value11</level11>
</root>
"""

class NextLevel(XmlBaseModel):
    level2: list[str] = XmlField(xpath="./level2/text()")


class MyModel(XmlBaseModel):
    next_level: NextLevel = XmlField(xpath="./level1")
    level_11: list[str] = XmlField(xpath="./level11/text()")


model = MyModel.model_validate_xml(xml_bytes)
print(model)
#> next_level=NextLevel(level2=['value1', 'value2', 'value3']) level_11=['value11']
```

## Development

Prerequisites:

- Any Python 3.8 through 3.12
- [poetry](https://github.com/python-poetry/poetry) for dependency management
- git
- make (to use the helper scripts in the Makefile)

Autoformatting can be applied by running

```bash
make lintable
```

Before commiting, remember to run

```bash
make lint
make test
```
