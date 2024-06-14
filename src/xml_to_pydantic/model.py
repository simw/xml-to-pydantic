from __future__ import annotations

from typing import Any, Callable, Iterable, cast

from lxml import etree
from pydantic import BaseModel, ValidationError
from pydantic import ConfigDict as BaseConfigDict
from pydantic.fields import FieldInfo
from typing_extensions import Self, get_args, get_origin

from .typing import _is_optional, _is_union


class XmlModelError(Exception):
    """Error in settings creating an XML model"""


class XmlParsingError(Exception):
    """Error when parsing XML using lxml"""


class ConfigDict(BaseConfigDict, total=False):
    xpath_generator: Callable[[str], str] | None
    xpath_root: str | None
    attribute_prefix: str


DEFAULT_CONFIG = ConfigDict(
    xpath_generator=None,
    xpath_root=None,
    attribute_prefix="attr_",
)


def XmlField(xpath: str, *args: Any, **kwargs: Any) -> Any:  # noqa: N802
    """
    Simlar to pydantic's Field function, this is needed to be able
    to return type Any, so as not to cause complaints by type checkers
    """
    return XmlFieldInfo(xpath, *args, **kwargs)


class XmlFieldInfo(FieldInfo):
    def __init__(self, xpath: str, *args: Any, **kwargs: Any):
        self.xpath = xpath
        super().__init__(*args, **kwargs)


def _generate_xpath(field: str, annotation: Any, config: ConfigDict) -> str:
    _, annotation = _is_optional(annotation)
    field_args = get_args(annotation)

    attr_prefix = config["attribute_prefix"]
    if field.startswith(attr_prefix):
        xpath = "@"
        field_path = field.replace(attr_prefix, "")
    else:
        xpath = "./"
        field_path = field

    xpath_gen = config["xpath_generator"]
    if xpath_gen is not None:
        field_path = xpath_gen(field_path)
    xpath = xpath + field_path

    if not (
        hasattr(annotation, "xml_fields")
        or (len(field_args) > 0 and hasattr(field_args[0], "xml_fields"))
        or field.startswith(attr_prefix)
    ):
        xpath += "/text()"

    return xpath


def _extract_field(items: list[etree._Element] | list[str], annotation: Any) -> Any:
    _, annotation = _is_optional(annotation)
    field_type = get_origin(annotation) or annotation
    field_args = get_args(annotation)

    # lxml always returns a list. If we want a single value,
    # we need to extract it
    result_as_list = (
        isinstance(field_type, type)
        and (not issubclass(field_type, (str, bytes, BaseModel)))
        and issubclass(field_type, Iterable)
    )

    # Is XmlBaseModel
    # Note: in python 3.9 -> 3.11, isinstance(list[str], type) is True, but
    # issubclass(list[str], XmlBaseModel) gives an exception.
    # Hence, duck typing may be a better solution here.
    if all(isinstance(item, str) for item in items):
        result: list[str] | list[dict[str, Any]] = cast(list[str], items)

    elif hasattr(field_type, "xml_fields"):
        items = cast(list[etree._Element], items)
        result = [_extract_model(item, field_type) for item in items]

    elif _is_union(field_type) and all(
        hasattr(arg, "xml_fields") for arg in field_args
    ):
        items = cast(list[etree._Element], items)
        result = []
        for arg in field_args:
            try:
                result = [_extract_model(item, arg) for item in items]
                result = [arg.model_validate(item) for item in result]
                break
            except ValidationError:  # pragam: no cover  # noqa: S110
                # Tests might not get here, as python / pydantic may not
                # preserve the ordering of the union type, so a test might
                # get the correct type on the first try
                pass  # pragma: no cover

    # Is eg list[XmlBaseModel]
    elif result_as_list and hasattr(field_args[0], "xml_fields"):
        items = cast(list[etree._Element], items)
        result = [_extract_model(item, field_args[0]) for item in items]

    else:
        raise XmlModelError(f"Unable to use type {annotation} in extraction.")

    if len(result) == 1 and not result_as_list:
        return result[0]

    return result


def _extract_model(root: etree._Element, cls: type[XmlBaseModel]) -> dict[str, Any]:
    xpath_root = cast(ConfigDict, cls.model_config).get("xpath_root")
    if xpath_root is not None:
        new_root = root.xpath(xpath_root)
        if len(new_root) != 1:
            raise XmlParsingError(
                f"Root xpath {cls.model_config.get('xpath_root')} did not "
                "return exactly one element"
            )
        root = new_root[0]

    extracted_data = {}
    try:
        for field_name, xpath in cls.xml_fields().items():
            annotation = cls.model_fields[field_name].annotation
            elements = root.xpath(xpath, smart_strings=False)
            if len(elements) == 0:
                continue
            extracted_data[field_name] = _extract_field(elements, annotation)

    except (AttributeError, etree.XPathError) as err:
        raise XmlParsingError(
            f"Error parsing field {field_name} on class {cls}"
        ) from err

    return extracted_data


class XmlBaseModel(BaseModel):
    @classmethod
    def xml_fields(cls) -> dict[str, str]:
        fields = {}
        config = ConfigDict(**{**DEFAULT_CONFIG, **cls.model_config})

        for field, info in cls.model_fields.items():
            if isinstance(info, XmlFieldInfo) and info.xpath is not None:
                xpath = info.xpath
            else:
                xpath = _generate_xpath(field, info.annotation, config)

            fields[field] = xpath

        return fields

    @classmethod
    def model_validate_xml(cls, xml: str | bytes | etree._Element) -> Self:
        if isinstance(xml, etree._Element):
            root = xml
        else:
            parser = etree.XMLParser()
            root = etree.fromstring(xml, parser=parser)  # noqa: S320

        extracted_data = _extract_model(root, cls)
        return cls.model_validate(extracted_data)

    @classmethod
    def model_validate_html(cls, html: str | bytes) -> Self:
        parser = etree.HTMLParser(recover=True)
        root = etree.fromstring(html, parser=parser)  # noqa: S320
        extracted_data = _extract_model(root, cls)
        return cls.model_validate(extracted_data)
