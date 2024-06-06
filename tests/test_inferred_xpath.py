from __future__ import annotations

from xml_to_pydantic import ConfigDict, XmlBaseModel


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

    class Element2Model(XmlBaseModel):
        element2a: str
        element2b: str

    class RootModel(XmlBaseModel):
        element1: str
        element2: Element2Model

    root_xpaths = {
        "element1": "./element1/text()",
        "element2": "./element2",
    }
    assert RootModel.xml_fields() == root_xpaths

    el2_xpaths = {
        "element2a": "./element2a/text()",
        "element2b": "./element2b/text()",
    }
    assert Element2Model.xml_fields() == el2_xpaths

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

    class Element2Model(XmlBaseModel):
        element2a: list[str]

    class RootModel(XmlBaseModel):
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

    class ElementModel(XmlBaseModel):
        subel: list[str]

    class RootModel(XmlBaseModel):
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

    class DashToUnderscore(XmlBaseModel):
        @staticmethod
        def xpath_generator(field_name: str) -> str:
            return field_name.replace("_", "-")

        model_config = ConfigDict(xpath_generator=xpath_generator)

    class Element2Model(DashToUnderscore):
        my_element_2a: list[str]

    class RootModel(DashToUnderscore):
        my_element_1: str
        my_element_2: Element2Model

    model = RootModel.model_validate_xml(xml_bytes)
    assert model.my_element_1 == "value1"
    assert model.my_element_2.my_element_2a == ["text1", "text2"]
