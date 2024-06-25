from __future__ import annotations

import types
from typing import Any, Union

from typing_extensions import get_args, get_origin


def _is_union(origin: Any) -> bool:
    """
    Function to determine if a type is a union, and to return the
    list of types stripped of the union.

    There are 3 (or 5) ways of declaring a union (depending on python version):
    1. Union[type1, type2]
    2. type1 | type2
    3. type1 & type2

    In python 3.10+, 'type1 | type2' has origin types.UnionType, but the others
    stick with typing.Union.
    """
    return (origin is Union) or (
        hasattr(types, "UnionType") and origin is types.UnionType
    )


def _is_optional(annotation: Any) -> tuple[bool, Any]:
    """
    Function to determine if a type is optional, and to return the
    type stripped of the optional.
    """
    if not _is_union(get_origin(annotation)):
        return False, annotation

    type_is_optional = False

    args = set(get_args(annotation))
    if type(None) in args:
        args.remove(type(None))
        type_is_optional = True

    if len(args) == 1:
        return type_is_optional, args.pop()

    return type_is_optional, Union[tuple(args)]
