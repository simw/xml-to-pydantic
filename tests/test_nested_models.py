from __future__ import annotations

import pydantic
import pytest

from xml_to_pydantic import XmlBaseModel, XmlField, XmlModelError


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


def test_optional_list_of_nested_models() -> None:
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
        element2: list[Model2] | None = XmlField(xpath="./element2")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2 is not None
    assert model.element2[0].element2a == "text1"
    assert model.element2[1].element2a == "text2"


def test_union_of_models_first_element() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
        </element2>
    </root>
    """

    class Model2(XmlBaseModel):
        element2a: str = XmlField(xpath="./element2a/text()")

    class Model3(XmlBaseModel):
        element3a: str = XmlField(xpath="./element3a/text()")

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
        element2: Model2 | Model3 = XmlField(xpath="./element2")

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert isinstance(model.element2, Model2)
    assert model.element2.element2a == "text1"


def test_union_of_models_second_element() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
        </element2>
    </root>
    """

    class Model2(XmlBaseModel):
        element2a: str

    class Model3(XmlBaseModel):
        element3a: str

    # Note: python (some versions? or pydantic?) does not preserve
    # the order of the Union.
    # If the underlying code only used the 1st element of the Union, then
    # it might pass some runs and fail some others.
    class MyModel(XmlBaseModel):
        element1: str
        element2: Model3 | Model2

    model = MyModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert isinstance(model.element2, Model2)
    assert model.element2.element2a == "text1"


def test_union_of_models_all_models_fail() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
        </element2>
    </root>
    """

    class Model3(XmlBaseModel):
        element3a: str

    class Model4(XmlBaseModel):
        element4a: str

    # Note: python (some versions? or pydantic?) does not preserve
    # the order of the Union.
    # If the underlying code only used the 1st element of the Union, then
    # it might pass some runs and fail some others.
    class MyModel(XmlBaseModel):
        element1: str
        element2: Model3 | Model4

    with pytest.raises(pydantic.ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_union_of_models_with_str() -> None:
    class Model2(XmlBaseModel):
        element2a: str = XmlField(xpath="./element2a/text()")

    class MyModel(XmlBaseModel):
        element1: str = XmlField(xpath="./element1/text()")
        element2: str | Model2 = XmlField(xpath="./element2")

    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
        </element2>
    </root>
    """
    with pytest.raises(XmlModelError) as exc_info:
        MyModel.model_validate_xml(xml_bytes)
    assert "Unable to use type" in str(exc_info)
