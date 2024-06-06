from __future__ import annotations

import types
from typing import Any, Callable, Iterable, Union, cast

from lxml import etree
from pydantic import BaseModel
from pydantic import ConfigDict as BaseConfigDict
from pydantic.fields import FieldInfo
from typing_extensions import Self, get_args, get_origin


class XmlModelError(Exception):
    """Error in settings creating an XML model"""


class XmlParsingError(Exception):
    """Error when parsing XML using lxml"""


class ConfigDict(BaseConfigDict):
    xpath_generator: Callable[[str], str]


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
            annotation = field_infos[field_name].annotation
            # eg1 if the annotation is list[str], get <class list>
            # eg2 if the annotation is str, get <class str>
            # eg3 if the annotation is list[str] | None, get field_type = Union
            field_type = get_origin(annotation) or annotation
            field_args = get_args(annotation)

            # Remove any optionality from the field type
            # Note: different versions of python have different ways of detecting
            # whether it's a Union / optional type
            if field_type is Union or (
                hasattr(types, "UnionType") and field_type is types.UnionType
            ):
                annotation = list(set(field_args) - {type(None)})[0]
                field_type = get_origin(annotation) or annotation
                field_args = get_args(annotation)

            if field_type is None:
                # Note pydantic will error on model creation before we even get here
                # But this makes mypy happy on the issubclass line later
                raise XmlModelError(
                    f"Field {field_name} has no type annotation"
                )  # pragma: no cover

            # In python 3.9 -> 3.11, isinstance(list[str], type) is True, but
            # issubclass(list[str], XmlBaseModel) gives an exception.
            # Hence, duck typing may be a better solution here.
            if hasattr(field_type, "xml_fields"):
                result = [extract_data(elem, field_type) for elem in result]

            elif len(field_args) > 0 and hasattr(field_args[0], "xml_fields"):
                result = [extract_data(elem, field_args[0]) for elem in result]

            # lxml always returns a list. If we want a single value,
            # we need to extract it
            result_as_list = (
                isinstance(field_type, type)
                and (not issubclass(field_type, (str, bytes, BaseModel)))
                and issubclass(field_type, Iterable)
            )

            if len(result) == 0:
                continue

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
            if isinstance(info, XmlFieldInfo) and info.xpath is not None:
                fields[field] = info.xpath
                continue

            # Need to check whether it's an XmlBaseModel
            # (or a list, or an optional ...)
            # If not, then should have /text() on the end, otherwise,
            # it's a nested model
            annotation = info.annotation
            field_type = get_origin(annotation) or annotation
            field_args = get_args(annotation)

            if field_type is Union or (
                hasattr(types, "UnionType") and field_type is types.UnionType
            ):
                annotation = list(set(field_args) - {type(None)})[0]
                field_type = get_origin(annotation) or annotation
                field_args = get_args(annotation)

            # TODO: add alias generator / support
            xpath = f"./{field}"
            xpath_gen = cast(
                Callable[[str], str], cls.model_config.get("xpath_generator")
            )
            if xpath_gen is not None:
                xpath = f"./{xpath_gen(field)}"

            if (
                hasattr(annotation, "xml_fields")
                or len(field_args) > 0
                and hasattr(field_args[0], "xml_fields")
            ):
                fields[field] = xpath
            else:
                fields[field] = xpath + "/text()"

        return fields

    @classmethod
    def model_validate_xml(cls, xml_bytes_or_str: str | bytes) -> Self:
        root = etree.XML(xml_bytes_or_str)
        extracted_data = extract_data(root, cls)
        return cls(**extracted_data)
