import configparser
import glob
import itertools
import os
import shutil
import warnings
from pathlib import Path

import click
from pytask import hookimpl
from pytask.shared import to_list


IGNORED_FILES_AND_FOLDERS = [
    "*/.git/*",
    "*/__pycache__/*",
    "*/.ipynb_checkpoints/*",
    "*/*.egg-info/*",
]


@hookimpl
def pytask_configure(pm, config_from_cli):
    config = {"pm": pm, "terminal_width": _get_terminal_width()}

    paths = _get_first_not_none_value(config_from_cli, key="paths", callback=to_list)
    paths = [Path(p).resolve() for path in paths for p in glob.glob(path.as_posix())]
    config["paths"] = paths if paths else [Path.cwd().resolve()]

    config["root"], config["ini"] = _find_project_root_and_ini(config["paths"])
    config_from_file = _read_config(config["ini"]) if config["ini"] is not None else {}

    config["pm"].hook.pytask_parse_config(
        config=config,
        config_from_cli=config_from_cli,
        config_from_file=config_from_file,
    )

    config["pm"].hook.pytask_post_parse(config=config)

    return config


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    config["ignore"] = (
        _get_first_not_none_value(
            config_from_cli,
            config_from_file,
            key="ignore",
            default=[],
            callback=to_list,
        )
        + IGNORED_FILES_AND_FOLDERS
    )

    config["debug_pytask"] = _get_first_not_none_value(
        config_from_cli, config_from_file, key="debug_pytask", default=False
    )
    if config["debug_pytask"]:
        config["pm"].trace.root.setwriter(click.echo)
        config["pm"].enable_tracing()

    provider = _get_first_not_none_value(
        config_from_cli, config_from_file, key="database_provider", default="sqlite"
    )
    filename = _get_first_not_none_value(
        config_from_cli,
        config_from_file,
        key="database_filename",
        default=".pytask.sqlite3",
    )
    create_db = _get_first_not_none_value(
        config_from_cli, config_from_file, key="database_create_db", default=True
    )
    create_tables = _get_first_not_none_value(
        config_from_cli, config_from_file, key="database_create_tables", default=True
    )
    config["database"] = {
        "provider": provider,
        "filename": Path(config["root"], filename).resolve().as_posix(),
        "create_db": create_db,
        "create_tables": create_tables,
    }


def _find_project_root_and_ini(paths):
    try:
        common_ancestor = Path(os.path.commonpath(paths))
    except ValueError:
        warnings.warn(
            "A common path for all passed path could not be detected. Fall back to "
            "current working directory."
        )
        common_ancestor = Path.cwd()

    config_path = None
    for parent, config_name in itertools.product(
        common_ancestor.parents, ["pytask.ini", "tox.ini", "setup.cfg"]
    ):
        path = parent.joinpath(config_name)

        if path.exists():
            config = configparser.ConfigParser()
            config.read(path)
            if "pytask" in config.sections():
                config_path = path
                break

    return common_ancestor, config_path


def _read_config(path):
    config = configparser.ConfigParser()
    config.read(path)
    return dict(config["pytask"])


def _get_first_not_none_value(*configs, key, default=None, callback=None):
    """Get the first non-None value for a key from a list of dictionaries.

    This function allows to prioritize information from many configurations by changing
    the order of the inputs while also providing a default.

    Examples
    --------
    >>> _get_first_not_none_value({"a": None}, {"a": 1}, key="a")
    1

    >>> _get_first_not_none_value({"a": None}, {"a": None}, key="a", default="default")
    'default'

    >>> _get_first_not_none_value({}, {}, key="a", default="default")
    'default'

    >>> _get_first_not_none_value({"a": None}, {"a": "b"}, key="a", callback=to_list)
    ['b']

    """
    return next(
        (
            config[key] if callback is None else callback(config[key])
            for config in configs
            if config.get(key, None) is not None
        ),
        default,
    )


def _get_terminal_width() -> int:
    width, _ = shutil.get_terminal_size(fallback=(80, 24))

    # The Windows get_terminal_size may be bogus, let's sanify a bit.
    if width < 40:
        width = 80

    return width
