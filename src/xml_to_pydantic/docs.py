from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Protocol, Union, cast

from cssselect import GenericTranslator, HTMLTranslator
from lxml import etree


class GenericDoc(Protocol):
    def query(
        self, query_type: Literal["xpath", "css"], query: str
    ) -> QueryReturn: ...  # pragma: no cover


# TODO: Add support for more types of queries - xpath can return bool, float
XPathReturn = Union[str, List[str], List[etree._Element]]
QueryReturn = Union[List[str], List[GenericDoc]]


@dataclass
class FieldQuery:
    query_type: Literal["xpath", "css"]
    query: str


class XpathDoc:
    def __init__(self, doc: etree._Element):
        self.doc = doc

    def _query(self, query: str) -> QueryReturn:
        results = cast(
            XPathReturn, self.doc.xpath(query, smart_strings=False)
        )  # noqa: S320

        if not isinstance(results, list):
            results = [results]

        query_results = [
            XmlDoc(result) if isinstance(result, etree._Element) else result
            for result in results
        ]

        return cast(QueryReturn, query_results)


class XmlDoc(XpathDoc):
    def __init__(self, doc: str | bytes | etree._Element):
        if not isinstance(doc, etree._Element):
            parser = etree.XMLParser()
            doc = etree.fromstring(doc, parser=parser)  # noqa: S320
        super().__init__(doc)

    def query(self, query_type: Literal["xpath", "css"], query: str) -> QueryReturn:
        if query_type not in ["xpath", "css"]:
            raise ValueError(
                f"Invalid query type for XmlDoc: {query_type}"
            )  # pragma: no cover

        if query_type == "css":
            query = GenericTranslator().css_to_xpath(query)
            query = f"{query}/text()"

        return self._query(query)


class HtmlDoc(XpathDoc):
    def __init__(self, doc: str | bytes | etree._Element):
        if not isinstance(doc, etree._Element):
            parser = etree.HTMLParser(recover=True)
            doc = etree.fromstring(doc, parser=parser)  # noqa: S320
        super().__init__(doc)

    def query(self, query_type: Literal["xpath", "css"], query: str) -> QueryReturn:
        if query_type not in ["xpath", "css"]:
            raise ValueError(
                f"Invalid query type for HtmlDoc: {query_type}"
            )  # pragma: no cover

        if query_type == "css":
            query = HTMLTranslator().css_to_xpath(query)
            query = f"{query}/text()"

        return self._query(query)
