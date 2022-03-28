from __future__ import annotations

import attr
from typed_settings.attrs import METADATA_KEY
from typed_settings.click_utils import DEFAULT_TYPES
from typed_settings.click_utils import TypeHandler


type_dict = {**DEFAULT_TYPES}


TYPE_HANDLER = TypeHandler(type_dict)


def option(
    *,
    default=attr.NOTHING,
    validator=None,
    repr=True,
    cmp=None,
    hash=None,
    init=True,
    metadata=None,
    type=None,
    converter=None,
    factory=None,
    kw_only=False,
    eq=None,
    order=None,
    on_setattr=None,
    help=None,
):
    """An alias to :func:`attr.field()`"""
    if help is not None:
        if metadata is None:
            metadata = {}
        metadata.setdefault(METADATA_KEY, {})["help"] = help

    return attr.ib(
        default=default,
        validator=validator,
        repr=repr,
        cmp=None,
        hash=hash,
        init=init,
        metadata=metadata,
        converter=converter,
        factory=factory,
        kw_only=kw_only,
        eq=eq,
        order=order,
        on_setattr=on_setattr,
    )
