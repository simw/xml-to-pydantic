import sys
from typing import Optional, Union

from xml_to_pydantic.typing import _is_optional


def test_str_is_optional() -> None:
    assert (False, str) == _is_optional(str)


def test_optional_str_is_optional() -> None:
    assert (True, str) == _is_optional(Optional[str])


def test_union_with_none_is_optional() -> None:
    assert (True, str) == _is_optional(Union[str, None])
    assert (True, str) == _is_optional(Union[None, str])


def test_or_none_is_optional() -> None:
    if sys.version_info >= (3, 10):
        assert (True, str) == _is_optional(str | None)
        assert (True, str) == _is_optional(None | str)


def test_union_two_types_not_optional() -> None:
    assert (False, Union[str, int]) == _is_optional(Union[str, int])


def test_union_single_type_not_optional() -> None:
    assert (False, str) == _is_optional(Union[str])
