from typing import List

import pytest
from pydantic import ValidationError

from xml_to_pydantic import CssField, DocModel


def test_basic_css_selector_on_html() -> None:
    html = b"""<!DOCTYPE html>
    <html>
        <head>
            <title>Title</title>
        </head>
        <body>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
        </body>
    </html>
    """

    class MyModel(DocModel):
        title: str = CssField(query="title")
        paragraphs: List[str] = CssField(query="p")

    model = MyModel.model_validate_html(html)
    assert model.title == "Title"
    assert model.paragraphs == ["Paragraph 1", "Paragraph 2"]


def test_basic_css_selector_on_xml() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element type="type1">text1</element>
        <element>4.53</element>
    </root>
    """

    class MyModel(DocModel):
        element: str = CssField(query="[type]")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element == "text1"


def test_css_selector_nested_model() -> None:
    html = b"""<!DOCTYPE html>
    <html>
        <head>
            <title>Title</title>
        </head>
        <body>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
        </body>
    </html>
    """

    class NestedModel(DocModel):
        paragraphs: List[str] = CssField(query="p")

    class MyModel(DocModel):
        title: str = CssField(query="title")
        body: NestedModel = CssField(query="body")

    # TODO: fix this test
    with pytest.raises(ValidationError):
        MyModel.model_validate_html(html)
