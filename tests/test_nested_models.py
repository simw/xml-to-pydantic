from __future__ import annotations

import pydantic
import pytest

from xml_to_pydantic import XmlBaseModel, XmlField


def test_nested_models() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
            <element2b>text2</element2b>
        </element2>
    </root>
    """

    class Model2(XmlBaseModel):
        element2a: str = XmlField(xpath="./element2a/text()")
        element2b: str = XmlField(xpath="./element2b/text()")

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
        element2: Model2 = XmlField(xpath="./element2")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2.element2a == "text1"
    assert model.element2.element2b == "text2"


def test_nested_models_direct_xml_value() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
            <element2b>text2</element2b>
        </element2>
    </root>
    """

    class Model2(XmlBaseModel):
        element2a: str
        element2b: str

        @classmethod
        def xml_fields(cls) -> dict[str, str]:
            return {
                "element2a": "./element2a/text()",
                "element2b": "./element2b/text()",
            }

    class MyModel(XmlBaseModel):
        element1: str
        element2: Model2

        @classmethod
        def xml_fields(cls) -> dict[str, str]:
            return {
                "element1": "./element1/text()",
                "element2": "./element2",
            }

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2.element2a == "text1"
    assert model.element2.element2b == "text2"


def test_nested_model_but_multiple_elements() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
        </element2>
        <element2>
            <element2a>text1</element2a>
        </element2>
    </root>
    """

    class Model2(XmlBaseModel):
        element2a: str = XmlField(xpath="./element2a/text()")

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
        element2: Model2 = XmlField(xpath="./element2")

    with pytest.raises(pydantic.ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_list_of_nested_models() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
        </element2>
        <element2>
            <element2a>text2</element2a>
        </element2>
    </root>
    """

    class Model2(XmlBaseModel):
        element2a: str = XmlField(xpath="./element2a/text()")

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
        element2: list[Model2] = XmlField(xpath="./element2")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2[0].element2a == "text1"
    assert model.element2[1].element2a == "text2"
