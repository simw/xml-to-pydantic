from __future__ import annotations

from typing import Any

from lxml import etree
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import Self


class XmlModelError(Exception):
    """Error in settings creating an XML model"""


class XmlParsingError(Exception):
    """Error when parsing XML using lxml"""


def XmlField(xpath: str, *args: Any, **kwargs: Any) -> Any:  # noqa: N802
    return XmlFieldInfo(xpath, *args, **kwargs)


class XmlFieldInfo(FieldInfo):
    def __init__(self, xpath: str, *args: Any, **kwargs: Any):
        self.xpath = xpath
        super().__init__(*args, **kwargs)


class XmlBaseModel(BaseModel):
    @classmethod
    def xml_fields(cls) -> dict[str, str]:
        fields = {}
        for field, info in cls.model_fields.items():
            if not isinstance(info, XmlFieldInfo) and info.is_required():
                raise XmlModelError(f"Field {field} is required but not an XmlField")
            if isinstance(info, XmlFieldInfo):
                fields[field] = info.xpath

        return fields

    @classmethod
    def model_validate_xml(cls, xml_bytes_or_str: str | bytes) -> Self:
        root = etree.XML(xml_bytes_or_str)
        data = {}
        try:
            for field, xpath in cls.xml_fields().items():
                result = root.xpath(xpath, smart_strings=False)
                if len(result) == 1:
                    data[field] = result[0]
                else:
                    data[field] = [elem.text for elem in result]
        except (AttributeError, etree.XPathError) as err:
            raise XmlParsingError(f"Error parsing field {field}") from err
        return cls(**data)
