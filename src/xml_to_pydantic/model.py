from __future__ import annotations

from typing import Any, Iterable

from lxml import etree
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import Self, get_origin


class XmlModelError(Exception):
    """Error in settings creating an XML model"""


class XmlParsingError(Exception):
    """Error when parsing XML using lxml"""


# Similar to pydantic's Field, this is needed to be
# able to return type Any, so as not to cause complaints
# by type checkers
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
        extracted_data = {}
        field_xpaths = cls.xml_fields()
        field_infos = cls.model_fields
        try:
            for field_name, xpath in field_xpaths.items():
                result = root.xpath(xpath, smart_strings=False)
                field_info = field_infos[field_name]
                # eg1 if the annotation is list[str], get <class list>
                # eg2 if the annotation is str, get <class str>
                field_type = get_origin(field_info.annotation) or field_info.annotation
                if field_type is None:
                    # Note pydantic will error on model creation before we even get here
                    # But this makes mypy happy on the issubclass line later
                    raise XmlModelError(
                        f"Field {field_name} has no type annotation"
                    )  # pragma: no cover

                # lxml always returns a list. If we want a single value,
                # we need to extract it
                result_as_list = (
                    not issubclass(field_type, (str, bytes))
                ) and issubclass(field_type, Iterable)
                if len(result) == 1 and not result_as_list:
                    extracted_data[field_name] = result[0]
                else:
                    extracted_data[field_name] = result
        except (AttributeError, etree.XPathError) as err:
            raise XmlParsingError(f"Error parsing field {field_name}") from err
        return cls(**extracted_data)
