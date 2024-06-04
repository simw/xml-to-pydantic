from __future__ import annotations

from typing import Any, Iterable

from lxml import etree
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import Self, get_args, get_origin


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


def extract_data(root: etree._Element, cls: type[XmlBaseModel]) -> dict[str, Any]:
    field_xpaths = cls.xml_fields()
    field_infos = cls.model_fields

    extracted_data = {}
    try:
        for field_name, xpath in field_xpaths.items():
            result = root.xpath(xpath, smart_strings=False)
            field_info = field_infos[field_name]
            # eg1 if the annotation is list[str], get <class list>
            # eg2 if the annotation is str, get <class str>
            field_type = get_origin(field_info.annotation) or field_info.annotation
            field_args = get_args(field_info.annotation)

            if field_type is None:
                # Note pydantic will error on model creation before we even get here
                # But this makes mypy happy on the issubclass line later
                raise XmlModelError(
                    f"Field {field_name} has no type annotation"
                )  # pragma: no cover

            if issubclass(field_type, BaseModel):
                result = [extract_data(elem, field_type) for elem in result]

            elif len(field_args) > 0 and issubclass(field_args[0], BaseModel):
                result = [extract_data(elem, field_args[0]) for elem in result]

            # lxml always returns a list. If we want a single value,
            # we need to extract it
            result_as_list = (
                not issubclass(field_type, (str, bytes, BaseModel))
            ) and issubclass(field_type, Iterable)

            if len(result) == 1 and not result_as_list:
                result = result[0]

            extracted_data[field_name] = result

    except (AttributeError, etree.XPathError) as err:
        raise XmlParsingError(
            f"Error parsing field {field_name} on class {cls}"
        ) from err

    return extracted_data


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
        extracted_data = extract_data(root, cls)
        return cls(**extracted_data)
