from __future__ import annotations

from typing import List, Literal, Optional

import pydantic
import pytest
from lxml import etree
from typing_extensions import Annotated

from xml_to_pydantic import ConfigDict, DocField, DocModel, DocParsingError, XpathField


def test_xml_parses_single_level_model() -> None:
    """Testing with a simple, single level model.

    This test defines the xpath in the model definition
    directly, in contrast to the next test where the xpath
    is written in the query_fields function."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element2>4.53</element2>
        <element3>56</element3>
        <element4 value="value4"/>
        <element5 value="value5">text5</element5>
    </root>
    """

    class MyModel(DocModel):
        element1: str = DocField(query_type="xpath", query="./element1/text()")
        element2: float = XpathField(query="./element2/text()")
        element3: int = XpathField(query="./element3/text()")
        element4_value: str = XpathField(query="./element4/@value")
        element5_value: str = XpathField(query="./element5/@value")
        element5: str = XpathField(query="./element5/text()")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "text1"
    assert model.element2 == 4.53  # noqa: PLR2004
    assert model.element3 == 56  # noqa: PLR2004
    assert model.element4_value == "value4"
    assert model.element5_value == "value5"
    assert model.element5 == "text5"


def test_xml_docfield_as_annotated() -> None:
    """
    Similar to pydantic, the (Xml)Field can be declared as
    Annotated, instead of as a field value.

    Note: pydantic deals with this itself when it constructs the
    model_fields dictionary.
    """

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element2>4.53</element2>
    </root>
    """

    class MyModel(DocModel):
        element1: Annotated[str, XpathField(query="./element1/text()")]
        element2: Annotated[float, XpathField(query="./element2/text()")]

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "text1"
    assert model.element2 == 4.53  # noqa: PLR2004


def test_field_without_annotation() -> None:
    with pytest.raises(pydantic.errors.PydanticUserError):

        class MyModel(DocModel):
            element1 = XpathField(query="./element1@value")


def test_invalid_xpath_fails() -> None:
    """If the xpath is invalid, then the library
    should raise the appropriate error (DocParsingError)."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(DocModel):
        element1: float = XpathField(query="./element1@value")

    with pytest.raises(DocParsingError):
        MyModel.model_validate_xml(xml_bytes)


def test_invalid_text_to_float() -> None:
    """If pydantic cannot do the conversion, then it should
    raise an error as per usual."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(DocModel):
        element1: float = XpathField(query="./element1/text()")

    with pytest.raises(pydantic.ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_list_to_str_fails() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element1>text2</element1>
    </root>
    """

    class MyModel(DocModel):
        element1: str = XpathField(query="./element1/text()")

    with pytest.raises(pydantic.ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_non_xml_field_not_required() -> None:
    """All fields need a value, and for DocModels this
    usually comes from the XML. But if there's a default
    value, then the xpath isn't required to be defined."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(DocModel):
        element1: str = XpathField(query="./element1/text()")
        element2: str | None = None
        element3: str = "default"

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "text1"


def test_parsing_multiple_elements_to_list() -> None:
    """
    Note: this tests both list and typing.List, which may
    not behave in the exact same way internally.
    """
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element1>text2</element1>
        <element2>4.1</element2>
        <element2>4.2</element2>
    </root>
    """

    class MyModel(DocModel):
        element1: list[str] = XpathField(query="./element1/text()")
        element2: List[float] = XpathField(query="./element2/text()")  # noqa: UP006

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == ["text1", "text2"]
    assert model.element2 == [4.1, 4.2]


def test_parsing_single_element_to_list() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element2>4.1</element2>
    </root>
    """

    class MyModel(DocModel):
        element1: list[str] = XpathField(query="./element1/text()")
        element2: list[float] = XpathField(query="./element2/text()")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == ["text1"]
    assert model.element2 == [4.1]


def test_optional_list() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element1>text2</element1>
        <element2>4.1</element2>
        <element2>4.2</element2>
    </root>
    """

    class MyModel(DocModel):
        element1: list[str] | None = XpathField(query="./element1/text()")
        element2: Optional[List[float]] = XpathField(  # noqa: UP006, UP007
            query="./element2/text()"
        )

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == ["text1", "text2"]
    assert model.element2 == [4.1, 4.2]


def test_literal() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
    </root>
    """

    class MyModel(DocModel):
        element1: Literal["value1", "value2"] = XpathField(query="./element1/text()")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"


def test_list_of_literals() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element1>value2</element1>
    </root>
    """

    class MyModel(DocModel):
        element1: list[Literal["value1", "value2"]] = XpathField(
            query="./element1/text()"
        )

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == ["value1", "value2"]


def test_empty_results() -> None:
    """
    If either a) the xpath element doesn't exist, or b) the xpath returns
    an empty list, then the field will drop out and will need a default
    value to be set.

    (Note: when using /text(), lxml xpath doesn't differentiate between an
    xpath element not existing and an xpath element existing but being empty)
    """

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1 />
    </root>
    """

    class MyModel(DocModel):
        no_element: str | None = XpathField(query="./noelement/text()", default=None)
        element1: str | None = XpathField(query="./element1/text()", default=None)
        element2: float | None = XpathField(query="./element1/text()", default=None)
        element3: int | None = XpathField(query="./element1/text()", default=None)
        element4: list[str] = XpathField(
            query="./element1/text()", default_factory=list
        )
        element5: list[str] | None = XpathField(query="./element1/text()", default=None)

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.no_element is None
    assert model.element1 is None
    assert model.element2 is None
    assert model.element3 is None
    assert model.element4 == []
    assert model.element5 is None


def test_empty_results_with_defaults() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
    </root>
    """

    class MyModel(DocModel):
        str_field: str = XpathField(query="/el/text()", default="default")
        opt_str_field: str | None = XpathField(query="/el/text()", default="default")
        list_field: list[str] = XpathField(
            query="/el/text()", default_factory=lambda: ["default"]
        )

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.str_field == "default"
    assert model.opt_str_field == "default"
    assert model.list_field == ["default"]


def test_passing_in_lxml_element_to_xml() -> None:
    from lxml import etree

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element2>4.1</element2>
    </root>
    """

    root = etree.fromstring(xml_bytes)

    class MyModel(DocModel):
        element1: str
        element2: float

    model = MyModel.model_validate_xml(root)
    assert model.element1 == "text1"
    assert model.element2 == 4.1  # noqa: PLR2004


def test_parsing_html() -> None:
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
        title: str = XpathField(query="/html/head/title/text()")
        paragraphs: list[str] = XpathField(query="/html/body/p/text()")

    model = MyModel.model_validate_html(html)
    assert model.title == "Title"
    assert model.paragraphs == ["Paragraph 1", "Paragraph 2"]


def test_passing_in_html_element() -> None:
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
        title: str = XpathField(query="/html/head/title/text()")
        paragraphs: list[str] = XpathField(query="/html/body/p/text()")

    root = etree.fromstring(html, parser=etree.HTMLParser())
    model = MyModel.model_validate_html(root)
    assert model.title == "Title"
    assert model.paragraphs == ["Paragraph 1", "Paragraph 2"]


def test_string_xpath_function_on_html() -> None:
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
        title: str = XpathField(query="string(/html/head/title)")

    model = MyModel.model_validate_html(html)
    assert model.title == "Title"


def test_string_xpath_function_on_xml() -> None:
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
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
        title: str = XpathField(query="string(/html/head/title)")

    model = MyModel.model_validate_xml(xml)
    assert model.title == "Title"


def test_xpath_root() -> None:
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
        model_config = ConfigDict(xpath_root="/html")
        title: str = XpathField(query="string(./head/title)")

    model = MyModel.model_validate_html(html)
    assert model.title == "Title"


def test_invalid_xpath_root() -> None:
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
        model_config = ConfigDict(xpath_root="string(/html)")
        title: str = XpathField(query="string(/head/title)")

    with pytest.raises(DocParsingError):
        MyModel.model_validate_html(html)
