# Getting Started

## Installation

Use pip or your favorite Python package manager (pipenv, poetry, pdm ...):

```bash
pip install xml-to-pydantic
```

## Usage

xml-to-pydantic is a library for Python to import HTML or XML into
Python objects and to validate the fields on those objects.

xml-to-pydantic builds on the functionality in the Pydantic library, but
applies the validation to HTML and XML, rather than to JSON and Python
dictionaries.

(At present, xml-to-pydantic only imports from XML or HTML, it cannot
export back.)

There are two approaches to processing and validating the HTML / XML:

1. Implying the XPath from the structure of the model
2. Specifying the XPath for each field

The first approach is simpler, and the second approach is more
flexible and allows arbitrarily complicated XPath expressions.

