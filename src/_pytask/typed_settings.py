from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any

import attr
import typed_settings as ts
from typed_settings.attrs import METADATA_KEY
from typed_settings.click_utils import DEFAULT_TYPES
from typed_settings.click_utils import TypeHandler
from typed_settings.exceptions import ConfigFileLoadError
from typed_settings.exceptions import ConfigFileNotFoundError
from typed_settings.types import OptionInfo


type_dict = {**DEFAULT_TYPES}
type_handler = TypeHandler(type_dict)


@attr.s
class IniFormat:
    """Read settings from an .ini formatted file."""

    section = attr.ib(type=str)

    def __call__(
        self, path: Path, _settings_cls: type, _options: list[OptionInfo]
    ) -> dict[str, Any]:
        sections = self.section.split(".")

        try:
            config = configparser.ConfigParser()
            config.read(path)
        except FileNotFoundError as e:
            raise ConfigFileNotFoundError(str(e)) from e
        for s in sections:
            try:
                settings = config[s]
            except KeyError:
                return {}
        return settings


file_loader = ts.FileLoader(
    formats={
        "*.cfg": IniFormat("pytask"),
        "*.ini": IniFormat("pytask"),
    },
    files=["setup.cfg", "tox.ini", "pytask.ini"],
)


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
    is_flag=None,
    help=None,
    param_decls=None,
    metavar=None,
):
    """An alias to :func:`attr.field()`"""
    for name, value in [
        ("help", help),
        ("param_decls", param_decls),
        ("is_flag", is_flag),
        ("metavar", metavar),
    ]:
        if value is not None:
            if metadata is None:
                metadata = {}
            metadata.setdefault(METADATA_KEY, {})[name] = value

    return attr.ib(
        default=default,
        validator=validator,
        repr=repr,
        cmp=None,
        hash=hash,
        init=init,
        metadata=metadata,
        type=type,
        converter=converter,
        factory=factory,
        kw_only=kw_only,
        eq=eq,
        order=order,
        on_setattr=on_setattr,
    )
