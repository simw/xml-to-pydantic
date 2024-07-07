from __future__ import annotations

import pytest

from xml_to_pydantic import ConfigDict, DocModel, DocParsingError


def test_inferring_xpath() -> None:
    """
    Instead of explicitly supplying the xpath, here we allow the
    model to infer it from the naming, similar to how pydantic
    infers aliases for python dictionaries / JSON.
    """
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
            <element2b>text2</element2b>
        </element2>
    </root>
    """

    class Element2Model(DocModel):
        element2a: str
        element2b: str

    class RootModel(DocModel):
        element1: str
        element2: Element2Model

    model = RootModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2.element2a == "text1"
    assert model.element2.element2b == "text2"


def test_inferring_xpath_with_list() -> None:
    """
    Instead of explicitly supplying the xpath, here we allow the
    model to infer it from the naming, similar to how pydantic
    infers aliases for python dictionaries / JSON.
    """
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>value1</element1>
        <element2>
            <element2a>text1</element2a>
            <element2a>text2</element2a>
        </element2>
    </root>
    """

    class Element2Model(DocModel):
        element2a: list[str]

    class RootModel(DocModel):
        element1: str
        element2: Element2Model

    model = RootModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2.element2a == ["text1", "text2"]


def test_inferring_xpath_with_list_of_models() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element>
            <subel>text1</subel>
        </element>
        <element>
            <subel>text2</subel>
        </element>
    </root>
    """

    class ElementModel(DocModel):
        subel: list[str]

    class RootModel(DocModel):
        element: list[ElementModel]

    model = RootModel.model_validate_xml(xml_bytes)
    assert model.element == [
        ElementModel(subel=["text1"]),
        ElementModel(subel=["text2"]),
    ]


def test_inferring_xpath_with_alias() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <my-element-1>value1</my-element-1>
        <my-element-2>
            <my-element-2a>text1</my-element-2a>
            <my-element-2a>text2</my-element-2a>
        </my-element-2>
    </root>
    """

    def xpath_generator(field_name: str) -> str:
        return field_name.replace("_", "-")

    class DashToUnderscore(DocModel):
        model_config = ConfigDict(xpath_generator=xpath_generator)

    class Element2Model(DashToUnderscore):
        my_element_2a: list[str]

    class RootModel(DashToUnderscore):
        my_element_1: str
        my_element_2: Element2Model

    model = RootModel.model_validate_xml(xml_bytes)
    assert model.my_element_1 == "value1"
    assert model.my_element_2.my_element_2a == ["text1", "text2"]


def test_inferring_xpath_with_new_root() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <new-root>
            <element1>value1</element1>
            <element2>
                <subel>
                    <element2a>text1</element2a>
                    <element2b>text2</element2b>
                </subel>
            </element2>
        </new-root>
    </root>
    """

    class Element2Model(DocModel):
        model_config = ConfigDict(xpath_root="./subel")
        element2a: str
        element2b: str

    class RootModel(DocModel):
        model_config = ConfigDict(xpath_root="./new-root")
        element1: str
        element2: Element2Model

    model = RootModel.model_validate_xml(xml_bytes)
    assert model.element1 == "value1"
    assert model.element2.element2a == "text1"
    assert model.element2.element2b == "text2"


def test_xpath_new_root_error_no_element() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <new-root>
            <element1>value1</element1>
        </new-root>
    </root>
    """

    class Model(DocModel):
        model_config = ConfigDict(xpath_root="./not-new-root")
        element1: str

    with pytest.raises(DocParsingError):
        Model.model_validate_xml(xml_bytes)


def test_xpath_new_root_error_two_elements() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <new-root>
            <element1>value1</element1>
        </new-root>
        <new-root>
            <element1>value2</element1>
        </new-root>
    </root>
    """

    class Model(DocModel):
        model_config = ConfigDict(xpath_root="./new-root")
        element1: str

    with pytest.raises(DocParsingError):
        Model.model_validate_xml(xml_bytes)


def test_xpath_attribute_model_field() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1 attribute="value1">
            <subel>text1</subel>
        </element1>
    </root>
    """

    class Element1(DocModel):
        attr_attribute: str
        subel: str

    class Model(DocModel):
        element1: Element1

    model = Model.model_validate_xml(xml_bytes)
    assert model.element1.attr_attribute == "value1"
    assert model.element1.subel == "text1"


def test_xpath_attribute_model_field_with_different_prefix() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1 attribute="value1">
            <subel>text1</subel>
        </element1>
    </root>
    """

    class Element1(DocModel):
        model_config = ConfigDict(attribute_prefix="at_")

        at_attribute: str
        subel: str

    class Model(DocModel):
        element1: Element1

    model = Model.model_validate_xml(xml_bytes)
    assert model.element1.at_attribute == "value1"
    assert model.element1.subel == "text1"
