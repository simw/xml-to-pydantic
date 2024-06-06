from __future__ import annotations

from typing import List, Literal, Optional

import pydantic
import pytest

from xml_to_pydantic import XmlBaseModel, XmlField, XmlParsingError


def test_xml_parses_single_level_model() -> None:
    """Testing with a simple, single level model.

    This test defines the xpath in the model definition
    directly, in contrast to the next test where the xpath
    is written in the xml_fields function."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element2>4.53</element2>
        <element3>56</element3>
        <element4 value="value4"/>
        <element5 value="value5">text5</element5>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
        element2: float = XmlField(xpath="./element2/text()")
        element3: int = XmlField(xpath="./element3/text()")
        element4_value: str = XmlField(xpath="./element4/@value")
        element5_value: str = XmlField(xpath="./element5/@value")
        element5: str = XmlField(xpath="./element5/text()")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "text1"
    assert model.element2 == 4.53  # noqa: PLR2004
    assert model.element3 == 56  # noqa: PLR2004


def test_xml_parses_direct_xml_fields() -> None:
    """Testing single level model, but with xpath
    defined in the xml_fields function, instead of on
    the model using XmlField.

    While more verbose, this might be prefered for separation
    of concerns or code readability for complex models."""
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element2>4.53</element2>
        <element3>56</element3>
        <element4 value="value4"/>
        <element5 value="value5">text5</element5>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: str
        element2: float
        element3: int
        element4_value: str
        element5_value: str
        element5: str

        @classmethod
        def xml_fields(cls) -> dict[str, str]:
            return {
                "element1": "./element1/text()",
                "element2": "./element2/text()",
                "element3": "./element3/text()",
                "element4_value": "./element4/@value",
                "element5_value": "./element5/@value",
                "element5": "./element5/text()",
            }

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "text1"
    assert model.element2 == 4.53  # noqa: PLR2004
    assert model.element3 == 56  # noqa: PLR2004


def test_field_without_annotation() -> None:
    with pytest.raises(pydantic.errors.PydanticUserError):

        class MyModel(XmlBaseModel):
            element1 = XmlField(xpath="./element1@value")


def test_invalid_xpath_fails() -> None:
    """If the xpath is invalid, then the library
    should raise the appropriate error (XmlParsingError)."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: float = XmlField(xpath="./element1@value")

    with pytest.raises(XmlParsingError):
        MyModel.model_validate_xml(xml_bytes)


def test_invalid_text_to_float() -> None:
    """If pydantic cannot do the conversion, then it should
    raise an error as per usual."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: float = XmlField(xpath="./element1/text()")

    with pytest.raises(pydantic.ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_list_to_str_fails() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element1>text2</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")

    with pytest.raises(pydantic.ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_non_xml_field_not_required() -> None:
    """All fields need a value, and for XmlBaseModels this
    usually comes from the XML. But if there's a default
    value, then the xpath isn't required to be defined."""

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
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

    class MyModel(XmlBaseModel):
        element1: list[str] = XmlField(xpath="./element1/text()")
        element2: List[float] = XmlField(xpath="./element2/text()")  # noqa: UP006

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

    class MyModel(XmlBaseModel):
        element1: list[str] = XmlField(xpath="./element1/text()")
        element2: list[float] = XmlField(xpath="./element2/text()")

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

    class MyModel(XmlBaseModel):
        element1: list[str] | None = XmlField(xpath="./element1/text()")
        element2: Optional[List[float]] = XmlField(  # noqa: UP006, UP007
            xpath="./element2/text()"
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

    class MyModel(XmlBaseModel):
        element1: Literal["value1", "value2"] = XmlField(xpath="./element1/text()")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"


def test_list_of_literals() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element1>value2</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: list[Literal["value1", "value2"]] = XmlField(
            xpath="./element1/text()"
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

    class MyModel(XmlBaseModel):
        no_element: str | None = XmlField(xpath="./noelement/text()", default=None)
        element1: str | None = XmlField(xpath="./element1/text()", default=None)
        element2: float | None = XmlField(xpath="./element1/text()", default=None)
        element3: int | None = XmlField(xpath="./element1/text()", default=None)
        element4: list[str] = XmlField(xpath="./element1/text()", default_factory=list)
        element5: list[str] | None = XmlField(xpath="./element1/text()", default=None)

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

    class MyModel(XmlBaseModel):
        str_field: str = XmlField(xpath="/el/text()", default="default")
        opt_str_field: str | None = XmlField(xpath="/el/text()", default="default")
        list_field: list[str] = XmlField(
            xpath="/el/text()", default_factory=lambda: ["default"]
        )

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.str_field == "default"
    assert model.opt_str_field == "default"
    assert model.list_field == ["default"]
