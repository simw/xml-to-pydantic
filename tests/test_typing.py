"""
This file demonstrates the behavior of isinstance, issubclass,
get_origin and get_args on some types. This behavior is relied
on when examining the type annotations of a field in a model.
"""

import sys
import types
from typing import Iterable, List, Literal, Optional, Union, get_args, get_origin

import pytest


def test_string() -> None:
    t = str

    assert t == str
    assert isinstance(t, type)
    assert issubclass(t, str)
    assert issubclass(t, Iterable)
    assert get_origin(t) is None
    assert get_args(t) == ()


def test_int() -> None:
    t = int

    assert t == int
    assert isinstance(t, type)
    assert issubclass(t, int)
    assert not issubclass(t, Iterable)
    assert get_origin(t) is None
    assert get_args(t) == ()


def test_list_no_type() -> None:
    t = list

    assert t == list
    assert isinstance(t, type)
    assert issubclass(t, list)
    assert issubclass(t, Iterable)
    assert get_origin(t) is None
    assert get_args(t) == ()


def test_list() -> None:
    if sys.version_info >= (3, 9):
        t = list[str]

        assert t == list[str]
        assert t != list

        if sys.version_info < (3, 11):
            assert isinstance(t, type)
        else:
            assert not isinstance(t, type)
        assert not issubclass(t, list)
        with pytest.raises(TypeError):
            issubclass(t, Iterable)

        assert get_origin(t) == list
        assert issubclass(get_origin(t), Iterable)

        assert get_args(t) == (str,)


def test_typing_list() -> None:
    t = List[str]

    assert t == List[str]
    if sys.version_info >= (3, 9):
        assert t != list[str]
    assert t != List
    assert t != list

    assert not isinstance(t, type)
    with pytest.raises(TypeError):
        issubclass(t, list)
    with pytest.raises(TypeError):
        issubclass(t, List)
    with pytest.raises(TypeError):
        issubclass(t, Iterable)

    assert isinstance(get_origin(t), type)
    assert get_origin(t) == list
    assert get_origin(t) != List
    assert issubclass(get_origin(t), Iterable)

    assert get_args(t) == (str,)


def test_literal() -> None:
    t = Literal["value1", "value2"]

    assert t == Literal["value1", "value2"]

    assert not isinstance(t, type)
    with pytest.raises(TypeError):
        issubclass(t, str)  # type: ignore
    with pytest.raises(TypeError):
        issubclass(t, Iterable)  # type: ignore

    assert get_origin(t) == Literal
    assert not isinstance(get_origin(t), type)
    with pytest.raises(TypeError):
        issubclass(get_origin(t), str)  # type: ignore

    assert get_args(t) == ("value1", "value2")
    assert all(isinstance(arg, str) for arg in get_args(t))


def test_optional() -> None:
    """
    Note that the three possible notations do not necessarily
    behave in the same way
    1. str | None
    2. Optional[str]
    3. Union[str, None]

    2. and 3. are very similar, except that the ordering of 3. could
    be reversed by the user (ie Union[None, str] vs Union[str, None])
    """
    if sys.version_info >= (3, 10):
        assert not isinstance(str | None, type)
        with pytest.raises(TypeError):
            issubclass(str | None, str)  # type: ignore
        assert get_origin(str | None) == types.UnionType
        assert isinstance(get_origin(str | None), type)
        assert not issubclass(get_origin(str | None), Iterable)
        assert get_args(str | None) == (str, type(None))
        assert get_args(None | str) == (type(None), str)

    assert not isinstance(Optional[str], type)
    with pytest.raises(TypeError):
        issubclass(Optional[str], str)  # type: ignore
    assert get_origin(Optional[str]) == Union
    assert not isinstance(get_origin(Optional[str]), type)
    with pytest.raises(TypeError):
        issubclass(get_origin(Optional[str]), Iterable)  # type: ignore
    assert get_args(Optional[str]) == (str, type(None))

    assert not isinstance(Union[str, None], type)
    with pytest.raises(TypeError):
        issubclass(Union[str, None], str)  # type: ignore
    assert get_origin(Union[str, None]) == Union
    assert not isinstance(get_origin(Union[str, None]), type)
    with pytest.raises(TypeError):
        issubclass(get_origin(Union[str, None]), Iterable)  # type: ignore
    assert get_args(Union[str, None]) == (str, type(None))
    assert get_args(Union[None, str]) == (type(None), str)
