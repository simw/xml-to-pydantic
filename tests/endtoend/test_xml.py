from __future__ import annotations

import datetime
from pathlib import Path

from pydantic import BeforeValidator
from typing_extensions import Annotated

from xml_to_pydantic import ConfigDict, DocModel, XpathField

DATA_DIR = Path(__file__).parent / "data"


def load_patents() -> list[bytes]:
    patents = []
    with open(DATA_DIR / "ipg240109_head.xml", "rb") as f:
        patent: list[bytes] = []
        for line in f:
            if line.startswith(b"<?xml"):
                if patent:
                    patents.append(b"".join(patent))
                patent = []
            patent.append(line)

    return patents


def test_simple_end_to_end() -> None:
    class Simple(DocModel):
        title: str = XpathField(
            query="/us-patent-grant/us-bibliographic-data-grant/invention-title/text()"
        )
        assignees: list[str] | None = XpathField(
            query="/us-patent-grant/us-bibliographic-data-grant/assignees/assignee/addressbook/orgname/text()",
            default=None,
        )
        claims: list[str] = XpathField(
            query="/us-patent-grant/claims/claim/claim-text/text()"
        )

    patents = load_patents()
    for patent in patents:
        simple = Simple.model_validate_xml(patent)
        assert simple.title
        assert simple.claims


def test_complex_end_to_end() -> None:
    def yyyymmdd_to_date(value: str) -> datetime.date:
        return datetime.datetime.strptime(value, "%Y%m%d").date()

    DateYyyymmdd = Annotated[  # noqa: N806 - ignore the snake_case warning
        datetime.date,
        BeforeValidator(yyyymmdd_to_date),
    ]

    def xpath_generator(field_name: str) -> str:
        return field_name.replace("_", "-")

    class DashToUnderscore(DocModel):
        model_config = ConfigDict(xpath_generator=xpath_generator)

    class PublicationRefDocId(DashToUnderscore):
        country: str
        doc_number: str
        kind: str
        date: DateYyyymmdd

    class PublicationReference(DashToUnderscore):
        document_id: PublicationRefDocId

    class AppRefDocId(DashToUnderscore):
        country: str
        doc_number: str
        date: DateYyyymmdd

    class ApplicationReference(DashToUnderscore):
        document_id: AppRefDocId

    class UsBiblioGraphicDataGrant(DashToUnderscore):
        publication_reference: PublicationReference
        application_reference: ApplicationReference

    class Root(DashToUnderscore):
        us_bibliographic_data_grant: UsBiblioGraphicDataGrant

    patents = load_patents()
    for patent in patents:
        root = Root.model_validate_xml(patent)
        assert root.us_bibliographic_data_grant is not None
