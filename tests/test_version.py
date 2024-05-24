import xml_to_pydantic


def test_version() -> None:
    assert xml_to_pydantic.__version__ is not None
