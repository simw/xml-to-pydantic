from __future__ import annotations

import types
from typing import Any, Union, get_args, get_origin


def _is_optional(annotation: Any) -> tuple[bool, Any]:
    """
    Function to determine if a type is optional, and to return the
    type stripped of the optional.

    There are 3 (or 5) ways of declaring an optional (depending on python version):
    1. Union[type, None] (or Union[None, type])
    2. Optional[type]
    3. type | None (or None | type)

    In python 3.10+, 'type | None' has origin types.UnionType, but the others
    stick with typing.Union.
    """
    origin = get_origin(annotation)

    is_union = (origin is Union) or (
        hasattr(types, "UnionType") and origin is types.UnionType
    )
    if not is_union:
        return False, annotation

    type_is_optional = False

    args = set(get_args(annotation))
    if type(None) in args:
        args.remove(type(None))
        type_is_optional = True

    if len(args) == 1:
        return type_is_optional, args.pop()

    return type_is_optional, Union[tuple(args)]
