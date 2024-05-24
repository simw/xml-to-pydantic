from typing import Dict

import pytest
from pydantic import ValidationError

from xml_to_pydantic import XmlBaseModel, XmlParsingError


def test_xml_parses() -> None:
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

        @staticmethod
        def xml_fields() -> Dict[str, str]:
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


def test_invalid_xpath_fails() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: float

        @staticmethod
        def xml_fields() -> Dict[str, str]:
            return {
                "element1": "./element1@value",
            }

    with pytest.raises(XmlParsingError):
        MyModel.model_validate_xml(xml_bytes)


def test_invalid_text_to_float() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: float

        @staticmethod
        def xml_fields() -> Dict[str, str]:
            return {
                "element1": "./element1",
            }

    with pytest.raises(ValidationError):
        MyModel.model_validate_xml(xml_bytes)


def test_list_to_float_fails() -> None:
    xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <element1>text1</element1>
        <element1>text2</element1>
    </root>
    """

    class MyModel(XmlBaseModel):
        element1: str

        @staticmethod
        def xml_fields() -> Dict[str, str]:
            return {
                "element1": "./element1",
            }

    with pytest.raises(ValidationError):
        MyModel.model_validate_xml(xml_bytes)
