from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import cast

import attrs
import click
import typed_settings as ts
from attrs import define
from attrs import field
from typed_settings.cli_click import OptionGroupFactory
from typed_settings.exceptions import ConfigFileLoadError
from typed_settings.exceptions import ConfigFileNotFoundError
from typed_settings.types import OptionList
from typed_settings.types import SettingsClass
from typed_settings.types import SettingsDict

from _pytask.click import ColoredCommand
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


@define
class SettingsBuilder:
    name: str
    function: Callable[..., Any]
    option_groups: dict[str, Any] = field(factory=dict)
    arguments: list[Any] = field(factory=list)

    def build_settings(self) -> Any:
        return ts.combine("Settings", Settings, self.option_groups)  # type: ignore[arg-type]

    def build_command(self, loaders: list[Loader]) -> Any:
        settings = self.build_settings()
        command = ts.click_options(
            settings, loaders, decorator_factory=OptionGroupFactory()
        )(self.function)
        command = click.command(name=self.name, cls=ColoredCommand)(command)
        command.params.extend(self.arguments)
        return command


_ALREADY_PRINTED_DEPRECATION_MSG: bool = False


class TomlFormat:
    """
    Support for TOML files.  Read settings from the given *section*.

    Args:
        section: The config file section to load settings from.
    """

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
        """
        Load settings from a TOML file and return them as a dict.

        Args:
            path: The path to the config file.
            options: The list of available settings.
            settings_cls: The base settings class for all options.  If ``None``, load
                top level settings.

        Return:
            A dict with the loaded settings.

        Raise:
            ConfigFileNotFoundError: If *path* does not exist.
            ConfigFileLoadError: If *path* cannot be read/loaded/decoded.
        """
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
            console.print(self.deprecated)
        settings["common.config_file"] = path
        settings["common.root"] = path.parent
        settings = self._rewrite_paths_of_options(settings, options)
        return cast(SettingsDict, settings)

    def _rewrite_paths_of_options(
        self, settings: SettingsDict, options: OptionList
    ) -> SettingsDict:
        """Rewrite paths of options in the settings."""
        option_paths = {option.path for option in options}
        for name in list(settings):
            if name in option_paths:
                continue

            for option_path in option_paths:
                if name in option_path:
                    settings[option_path] = settings.pop(name)
                    break

        return settings


def load_settings(settings_cls: Any) -> Any:
    """Load the settings."""
    loaders = create_settings_loaders()
    return ts.load_settings(settings_cls, loaders)


def create_settings_loaders() -> list[Loader]:
    """Create the loaders for the settings."""
    return [
        ts.FileLoader(
            files=[ts.find("pyproject.toml")],
            env_var=None,
            formats={
                "*.toml": TomlFormat(
                    section="tool.pytask.ini_options",
                    deprecated=(
                        "[skipped]Deprecation Warning! Configuring pytask in the "
                        r"section \[tool.pytask.ini_options] is deprecated and will be "
                        r"removed in v0.6. Please, use \[tool.pytask] instead.[/]\n\n"
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
    ]


def update_settings(settings: Any, updates: dict[str, Any]) -> Any:
    """Update the settings recursively with some updates."""
    names = [i for i in dir(settings) if not i.startswith("_")]
    for name in names:
        if name in updates:
            value = updates[name]
            if value in ((), []):
                continue

            setattr(settings, name, updates[name])

        if attrs.has(getattr(settings, name)):
            update_settings(getattr(settings, name), updates)

    return settings
