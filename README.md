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

To process and validate XML into pydantic models would then require
two steps: convert the XML to a Python dictionary, then convert to
the pydantic model. This libary provides a way to combine those steps.

Note: if you are using this library to parse external, uncontrolled XML, you should
be aware of possible attack vectors through XML: [https://github.com/tiran/defusedxml].
This library uses lxml under the hood.

## Installation

Use pip, or your favorite Python package manager (pipenv, poetry, pdm, ...):

```bash
pip install xml-to-pydantic
```

## Usage

An example

```py
import xml_to_pydantic

print("An example!")
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
