from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import cast

import attrs
import click
import typed_settings as ts
from attrs import define
from attrs import field
from pluggy import PluginManager
from typed_settings.cli_click import OptionGroupFactory
from typed_settings.exceptions import ConfigFileLoadError
from typed_settings.exceptions import ConfigFileNotFoundError
from typed_settings.types import LoadedSettings
from typed_settings.types import LoaderMeta
from typed_settings.types import OptionList
from typed_settings.types import SettingsClass
from typed_settings.types import SettingsDict

from _pytask.console import console
from _pytask.settings import Settings

if TYPE_CHECKING:
    from pathlib import Path

    from typed_settings.loaders import Loader

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


__all__ = ["SettingsBuilder", "TomlFormat"]


def _handle_enum(type: type[Enum], default: Any, is_optional: bool) -> dict[str, Any]:  # noqa: A002
    """Use enum values as choices for click options."""
    kwargs: dict[str, Any] = {"type": click.Choice([i.value for i in type])}
    if isinstance(default, type):
        kwargs["default"] = default.value
    elif is_optional:
        kwargs["default"] = None
    return kwargs


@define
class SettingsBuilder:
    commands: dict[str, Callable[..., Any]] = field(factory=dict)
    option_groups: dict[str, Any] = field(factory=dict)
    arguments: list[Any] = field(factory=list)

    def build_settings(self) -> Any:
        return ts.combine("Settings", Settings, self.option_groups)  # type: ignore[arg-type]

    def load_settings(self, kwargs: dict[str, Any]) -> Any:
        settings = self.build_settings()
        return ts.load_settings(
            settings,
            create_settings_loaders(kwargs=kwargs),
            converter=create_converter(),
        )

    def build_decorator(self) -> Any:
        settings = self.build_settings()

        type_dict = {**ts.cli_click.DEFAULT_TYPES, Enum: _handle_enum}
        type_handler = ts.cli_click.ClickHandler(type_dict)

        return ts.click_options(
            settings,
            create_settings_loaders(),
            converter=create_converter(),
            decorator_factory=OptionGroupFactory(),
            type_args_maker=ts.cli_utils.TypeArgsMaker(type_handler),
        )


_ALREADY_PRINTED_DEPRECATION_MSG: bool = False


class TomlFormat:
    """Support for TOML files."""

    def __init__(
        self,
        section: str | None,
        exclude: list[str] | None = None,
        deprecated: str = "",
    ) -> None:
        self.section = section
        self.exclude = exclude or []
        self.deprecated = deprecated

    def __call__(
        self,
        path: Path,
        settings_cls: SettingsClass,  # noqa: ARG002
        options: OptionList,
    ) -> SettingsDict:
        """Load settings from a TOML file and return them as a dict."""
        try:
            with path.open("rb") as f:
                settings = tomllib.load(f)
        except FileNotFoundError as e:
            raise ConfigFileNotFoundError(str(e)) from e
        except (PermissionError, tomllib.TOMLDecodeError) as e:
            raise ConfigFileLoadError(str(e)) from e
        if self.section is not None:
            sections = self.section.split(".")
            for s in sections:
                try:
                    settings = settings[s]
                except KeyError:  # noqa: PERF203
                    return {}
        for key in self.exclude:
            settings.pop(key, None)

        global _ALREADY_PRINTED_DEPRECATION_MSG  # noqa: PLW0603
        if self.deprecated and not _ALREADY_PRINTED_DEPRECATION_MSG:
            _ALREADY_PRINTED_DEPRECATION_MSG = True
            console.print(self.deprecated, style="skipped")
        settings["common.config_file"] = path
        settings["common.root"] = path.parent
        settings = _rewrite_paths_of_options(settings, options, section=self.section)
        return cast(SettingsDict, settings)


class DictLoader:
    """Load settings from a dict of values."""

    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings

    def __call__(
        self,
        settings_cls: SettingsClass,  # noqa: ARG002
        options: OptionList,
    ) -> LoadedSettings:
        settings = _rewrite_paths_of_options(self.settings, options, section=None)
        nested_settings: dict[str, dict[str, Any]] = {
            name.split(".")[0]: {} for name in settings
        }
        for long_name, value in settings.items():
            group, name = long_name.split(".")
            nested_settings[group][name] = value
        return LoadedSettings(nested_settings, LoaderMeta(self))


def load_settings(settings_cls: Any, kwargs: dict[str, Any] | None = None) -> Any:
    """Load the settings."""
    loaders = create_settings_loaders(kwargs=kwargs)
    converter = create_converter()
    return ts.load_settings(settings_cls, loaders, converter=converter)


def _convert_to_enum(val: Any, cls: type[Enum]) -> Enum:
    if isinstance(val, Enum):
        return val
    try:
        return cls(val)
    except ValueError:
        values = ", ".join([i.value for i in cls])
        msg = (
            f"{val!r} is not a valid value for {cls.__name__}. Use one of {values} "
            "instead."
        )
        raise ValueError(msg) from None


def create_converter() -> ts.Converter:
    """Create the converter."""
    converter = ts.converters.get_default_ts_converter()
    converter.scalar_converters[Enum] = _convert_to_enum
    converter.scalar_converters[PluginManager] = (
        lambda val, cls: val if isinstance(val, cls) else cls(**val)
    )
    return converter


def create_settings_loaders(kwargs: dict[str, Any] | None = None) -> list[Loader]:
    """Create the loaders for the settings."""
    kwargs_ = kwargs or {}
    return [
        ts.FileLoader(
            files=[ts.find("pyproject.toml")],
            env_var=None,
            formats={
                "*.toml": TomlFormat(
                    section="tool.pytask.ini_options",
                    deprecated=(
                        "DeprecationWarning: Configuring pytask in the "
                        "section \\[tool.pytask.ini_options] is deprecated and will be "
                        "removed in v0.6. Please, use \\[tool.pytask] instead."
                    ),
                )
            },
        ),
        ts.FileLoader(
            files=[ts.find("pyproject.toml")],
            env_var=None,
            formats={
                "*.toml": TomlFormat(section="tool.pytask", exclude=["ini_options"])
            },
        ),
        ts.EnvLoader(prefix="PYTASK_", nested_delimiter="_"),
        DictLoader(kwargs_),
    ]


def update_settings(settings: Any, updates: dict[str, Any]) -> Any:
    """Update the settings recursively with some updates."""
    names = [i for i in dir(settings) if not i.startswith("_")]
    for name in names:
        if attrs.has(getattr(settings, name)):
            update_settings(getattr(settings, name), updates)
            continue

        if name in updates:
            value = updates[name]
            if value in ((), []):
                continue
            setattr(settings, name, updates[name])
    return settings


def convert_settings_to_kwargs(settings: Settings) -> dict[str, Any]:
    """Convert the settings to kwargs."""
    kwargs: dict[str, Any] = {}
    names = [i for i in dir(settings) if not i.startswith("_")]
    for name in names:
        kwargs = kwargs | attrs.asdict(getattr(settings, name))
    return kwargs


def _rewrite_paths_of_options(
    settings: SettingsDict, options: OptionList, section: str | None
) -> SettingsDict:
    """Rewrite paths of options in the settings."""
    option_paths = {option.path for option in options}
    option_name_to_path = {
        option.path.rsplit(".", maxsplit=1)[1]: option.path for option in options
    }

    new_settings = {}
    for name, value in settings.items():
        if name in option_paths:
            new_settings[name] = value
            continue

        if name in option_name_to_path:
            new_path = option_name_to_path[name]
            if section:
                subsection, _ = new_path.rsplit(".", maxsplit=1)
                msg = (
                    f"DeprecationWarning: The path of the option {name!r} changed from "
                    f"\\[{section}] to the new path \\[tool.pytask.{subsection}]."
                )
                console.print(msg, style="skipped")
            new_settings[new_path] = value

    return new_settings