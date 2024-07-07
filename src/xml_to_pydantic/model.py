from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Literal, Union, cast

from lxml import etree
from pydantic import BaseModel, ValidationError
from pydantic import ConfigDict as BaseConfigDict
from pydantic.fields import FieldInfo
from typing_extensions import Self, get_args, get_origin

from .docs import FieldQuery, GenericDoc, HtmlDoc, XmlDoc
from .typing import _is_optional, _is_union

QueryTypes = Literal["xpath", "css"]


class DocModelError(Exception):
    """Error in settings creating an XML model"""


class DocParsingError(Exception):
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


def DocField(  # noqa: N802
    query_type: QueryTypes, query: str, *args: Any, **kwargs: Any
) -> Any:
    """
    Simlar to pydantic's Field function, this is needed to be able
    to return type Any, so as not to cause complaints by type checkers
    """
    return DocFieldInfo(query_type, query, *args, **kwargs)


def CssField(query: str, *args: Any, **kwargs: Any) -> Any:  # noqa: N802
    return DocFieldInfo("css", query, *args, **kwargs)


def XpathField(query: str, *args: Any, **kwargs: Any) -> Any:  # noqa: N802
    return DocFieldInfo("xpath", query, *args, **kwargs)


class DocFieldInfo(FieldInfo):
    def __init__(self, query_type: QueryTypes, query: str, *args: Any, **kwargs: Any):
        self.query_type = query_type
        self.query = query
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
        hasattr(annotation, "query_fields")
        or (len(field_args) > 0 and hasattr(field_args[0], "query_fields"))
        or field.startswith(attr_prefix)
    ):
        xpath += "/text()"

    return xpath


def _extract_field(
    items: list[GenericDoc] | list[str], annotation: Any
) -> str | list[str] | dict[str, Any] | list[dict[str, Any]]:
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

    # Is DocModel
    # Note: in python 3.9 -> 3.11, isinstance(list[str], type) is True, but
    # issubclass(list[str], DocModel) gives an exception.
    # Hence, duck typing may be a better solution here.
    if all(isinstance(item, str) for item in items):
        result = cast(Union[List[str], List[Dict[str, Any]]], items)

    elif hasattr(field_type, "query_fields"):
        items = cast(List[GenericDoc], items)
        result = [_extract_model(item, field_type) for item in items]

    elif _is_union(field_type) and all(
        hasattr(arg, "query_fields") for arg in field_args
    ):
        items = cast(List[GenericDoc], items)
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

    # Is eg list[DocModel]
    elif result_as_list and hasattr(field_args[0], "query_fields"):
        items = cast(List[GenericDoc], items)
        result = [_extract_model(item, field_args[0]) for item in items]

    else:
        msg = f"Unable to use type {annotation} in extraction "
        msg += f"from items ({type(items[0])} ...)"
        raise DocModelError(msg)

    if len(result) == 1 and not result_as_list:
        return result[0]

    return result


def _extract_model(doc: GenericDoc, cls: type[DocModel]) -> dict[str, Any]:
    xpath_root = cast(ConfigDict, cls.model_config).get("xpath_root")
    if xpath_root is not None:
        new_docs = doc.query("xpath", xpath_root)
        if len(new_docs) != 1:
            raise DocParsingError(
                f"Root xpath {cls.model_config.get('xpath_root')} did not "
                "return exactly one element"
            )
        if not isinstance(new_docs[0], (HtmlDoc, XmlDoc)):
            raise DocParsingError(
                f"Root xpath {cls.model_config.get('xpath_root')} did not "
                f"return an element, returned a {type(new_docs[0])} instead"
            )
        doc = new_docs[0]

    extracted_data = {}
    try:
        for field_name, query in cls.query_fields().items():
            annotation = cls.model_fields[field_name].annotation
            elements = doc.query(query.query_type, query.query)
            if len(elements) == 0:
                continue
            extracted_data[field_name] = _extract_field(elements, annotation)

    except (AttributeError, etree.XPathError) as err:
        raise DocParsingError(
            f"Error parsing field {field_name} on class {cls}"
        ) from err

    return extracted_data


class DocModel(BaseModel):
    @classmethod
    def query_fields(cls) -> dict[str, FieldQuery]:
        fields = {}
        config = ConfigDict(**{**DEFAULT_CONFIG, **cls.model_config})

        for field, info in cls.model_fields.items():
            if isinstance(info, DocFieldInfo) and info.query is not None:
                query_type = info.query_type
                query = info.query
            else:
                query_type = "xpath"
                query = _generate_xpath(field, info.annotation, config)

            fields[field] = FieldQuery(query_type=query_type, query=query)

        return fields

    @classmethod
    def model_validate_xml(cls, xml: str | bytes | etree._Element) -> Self:
        doc = XmlDoc(xml)
        extracted_data = _extract_model(doc, cls)
        return cls.model_validate(extracted_data)

    @classmethod
    def model_validate_html(cls, html: str | bytes | etree._Element) -> Self:
        doc = HtmlDoc(html)
        extracted_data = _extract_model(doc, cls)
        return cls.model_validate(extracted_data)
