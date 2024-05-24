from __future__ import annotations

from lxml import etree
from pydantic import BaseModel
from typing_extensions import Self


class XmlParsingError(Exception):
    """Error when parsing XML using lxml"""


class XmlBaseModel(BaseModel):
    @staticmethod
    def xml_fields() -> dict[str, str]:
        raise NotImplementedError

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
