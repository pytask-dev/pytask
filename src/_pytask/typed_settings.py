from __future__ import annotations

import configparser
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any
from typing import MutableMapping
from typing import TypeVar

import attr
import click
import typed_settings as ts
from _pytask.models import PathType
from typed_settings._dict_utils import _merge_dicts
from typed_settings.attrs import METADATA_KEY
from typed_settings.click_utils import DEFAULT_TYPES
from typed_settings.click_utils import TypeHandler
from typed_settings.exceptions import ConfigFileLoadError
from typed_settings.exceptions import ConfigFileNotFoundError
from typed_settings.types import OptionInfo


SettingsDict = MutableMapping[str, Any]
ET = TypeVar("ET", bound=Enum)


def handle_enum(type: Type[Enum], default: Any) -> dict[str, Any]:
    """
    Use :class:`EnumChoice` as option type and use the enum value's name as
    default.
    """
    type_info = {"type": click.Choice([e.value for e in type])}
    if default is not attr.NOTHING:
        # Convert Enum instance to string
        type_info["default"] = default.value

    return type_info


def handle_path_type(type: PathType, default: Any) -> dict[str, Any]:
    """
    Use :class:`EnumChoice` as option type and use the enum value's name as
    default.
    """
    type_info = {"type": type}
    if default is not attr.NOTHING:
        type_info["default"] = default
    return type_info


type_dict = {**DEFAULT_TYPES, Enum: handle_enum}
type_handler = TypeHandler(type_dict)


def to_enum(value: Any, cls: Type[ET]) -> ET:
    """
    Return a converter that creates an instance of the :class:`.Enum` *cls*.

    If the to be converted value is not already an enum, the converter will
    create one by name (``MyEnum[val]``).

    Args:
        value: The input data
        cls: The enum type

    Return:
        An instance of *cls*

    Raise:
        KeyError: If *value* is not a valid member of *cls*

    """
    if isinstance(value, cls):
        return value
    elif isinstance(value, str) and value in cls.__members__:
        return cls[value]
    elif isinstance(value, str) and value in [e.value for e in cls]:
        key = {e.value: e.name for e in cls}[value]
        return cls[key]
    else:
        raise Value(f"Cannot convert {value} of type {cls}.")


def to_list_of_paths(value: Any, cls: PathType) -> PathType:
    if isinstance(value, str):
        value = value.split("n")
    elif isinstance(value, Path):
        value = [value]

    return [Path(x) for x in value]


converter = ts.default_converter()
converter.register_structure_hook(Enum, to_enum)
converter.register_structure_hook(PathType, to_list_of_paths)


@attr.s
class IniFormat:
    """Read settings from an .ini formatted file.

    If a configuration was found, add the path to the configuration as a value.

    """

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
        else:
            settings = dict(settings)
            settings["config"] = path
        return settings


class FileLoader(ts.FileLoader):
    def __call__(self, settings_cls: type, options: list[OptionInfo]) -> SettingsDict:
        """
        Load settings for the given options.

        This search process stops as soon as the first configuration file with a
        ``[pytask]`` section is found.

        Parameters
        ----------
        settings_cls : type
            The base settings class for all options.
        options : list[OptionInfo]
            The list of available settings.

        Raise
        -----
        UnknownFormat:
            When no :class:`FileFormat` is configured for a loaded file.
        ConfigFileNotFoundError:
            If *path* does not exist.
        ConfigFileLoadError:
            If *path* cannot be read/loaded/decoded.
        InvalidOptionError:
            If invalid settings have been found.

        Returns
        -------
        dict[str, Any]
            A dict with the loaded settings.
        """
        paths = self._get_config_filenames(self.files, self.env_var)
        for path in paths:
            settings = self._load_file(path, settings_cls, options)
            if "config" in settings:
                break
        return settings

    def _load_file(
        self,
        path: Path,
        settings_cls: type,
        options: list[OptionInfo],
    ) -> SettingsDict:
        """
        Load a file and return its cleaned contents
        """
        # "clean_settings()" must be called for each loaded file individually
        # because of the "-"/"_" normalization.  This also allows us to tell
        # the user the exact file that contains errors.
        for pattern, ffloader in self.formats.items():
            if fnmatch(path.name, pattern):
                settings = ffloader(path, settings_cls, options)
                settings = self.clean_settings(settings, options, path)
                return settings

        raise UnknownFormatError(f"No loader configured for: {path}")

    @staticmethod
    def clean_settings(
        settings: SettingsDict, options: list[OptionInfo], source: Any
    ) -> SettingsDict:
        """
        Recursively check settings for invalid entries and raise an error.

        An error is not raised until all options have been checked.  It then lists
        all invalid options that have been found.

        Args:
            settings: The settings to be cleaned.
            options: The list of available settings.
            source: Source of the settings (e.g., path to a config file).
                    It should have a useful string representation.

        Return:
            The cleaned settings.
        Raise:
            InvalidOptionError: If invalid settings have been found.
        """
        invalid_paths = []
        valid_paths = {o.path for o in options}
        cleaned: SettingsDict = {}

        def _iter_dict(d: SettingsDict, prefix: str) -> None:
            for key, val in d.items():
                key = key.replace("-", "_")
                path = f"{prefix}{key}"

                if path in valid_paths:
                    _set_path(cleaned, path, val)
                    continue

                if isinstance(val, dict):
                    _iter_dict(val, f"{path}.")
                else:
                    invalid_paths.append(path)

        _iter_dict(settings, "")

        # if invalid_paths:
        #     joined_paths = ", ".join(sorted(invalid_paths))
        #     raise InvalidOptionsError(
        #         f"Invalid options found in {source}: {joined_paths}"
        #     )

        return cleaned


def _set_path(dct: SettingsDict, path: str, val: Any) -> None:
    """
    Sets a value to a nested dict and automatically creates missing dicts
    should they not exist.

    Calling ``_set_path(dct, "a.b", 3)`` is equivalent to ``dict["a"]["b"]
    = 3``.

    Args:
        dct: The dict that should contain the value
        path: The (nested) path, a dot-separated concatenation of keys.
        val: The value to set
    """
    *parts, key = path.split(".")
    for part in parts:
        dct = dct.setdefault(part, {})
    dct[key] = val


file_loader = FileLoader(
    formats={
        "*.cfg": IniFormat("pytask"),
        "*.ini": IniFormat("pytask"),
    },
    files=[ts.find("pytask.ini"), ts.find("tox.ini"), ts.find("setup.cfg")],
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
    hidden=False,
):
    """An alias to :func:`attr.field()`"""
    for name, value in [
        ("help", help),
        ("param_decls", param_decls),
        ("is_flag", is_flag),
        ("metavar", metavar),
        ("hidden", hidden),
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
