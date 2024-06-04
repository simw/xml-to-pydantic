# xml-to-pydantic

[![CI](https://github.com/simw/xml-to-pydantic/actions/workflows/test.yml/badge.svg?event=push)](https://github.com/simw/xml-to-pydantic/actions/workflows/test.yml)
[![pypi](https://img.shields.io/pypi/v/xml-to-pydantic.svg)](https://pypi.python.org/pypi/xml-to-pydantic)
[![versions](https://img.shields.io/pypi/pyversions/xml-to-pydantic.svg)](https://github.com/simw/xml-to-pydantic)
[![license](https://img.shields.io/github/license/simw/xml-to-pydantic.svg)](https://github.com/simw/xml-to-pydantic/blob/main/LICENSE)

xml-to-pydantic is a library for Python to convert XML to pydantic
models. 

(Please note that this project is not affiliated in any way with the
great team at [pydantic](https://github.com/pydantic/pydantic).)

[pydantic](https://github.com/pydantic/pydantic) is a Python library
for data validation, applying type hints / annotations. It enables
the creation of easy or complex data validation rules for processing
external data. That data usually comes in JSON format or from a Python
dictionary.

But to process and validate XML into pydantic models would then require
two steps: convert the XML to a Python dictionary, then convert to
the pydantic model. This libary provides a convenient way to combine those steps.

Note: if you are using this library to parse external, uncontrolled XML, you should
be aware of possible attack vectors through XML: [https://github.com/tiran/defusedxml].
This library uses lxml under the hood.

## Installation

Use pip, or your favorite Python package manager (pipenv, poetry, pdm, ...):

```bash
pip install xml-to-pydantic
```

## Usage

The XML is extracted using XPath defined on the fields:

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
# > number=4.53 href='https://example.com'
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
# > next_level=NextLevel(level2=['value1', 'value2', 'value3']) level_11=['value11']
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
