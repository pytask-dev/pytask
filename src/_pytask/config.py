import configparser
import glob
import itertools
import os
import shutil
import warnings
from pathlib import Path

import click
import pluggy
from _pytask.shared import get_first_not_none_value
from _pytask.shared import parse_value_or_multiline_option
from _pytask.shared import to_list


hookimpl = pluggy.HookimplMarker("pytask")


IGNORED_FILES_AND_FOLDERS = [
    "*/.git/*",
    "*/__pycache__/*",
    "*/.ipynb_checkpoints/*",
    "*/*.egg-info/*",
]


@hookimpl
def pytask_extend_command_line_interface(cli):
    cli.commands["build"].params.append(
        click.Option(
            ["-c", "--config"],
            type=click.Path(exists=True),
            help="Path to configuration file.",
        )
    )


@hookimpl
def pytask_configure(pm, config_from_cli):
    config = {"pm": pm, "terminal_width": _get_terminal_width()}

    paths = get_first_not_none_value(
        config_from_cli, key="paths", default=[Path.cwd()], callback=to_list
    )
    paths = [Path(p).resolve() for path in paths for p in glob.glob(path.as_posix())]
    config["paths"] = paths if paths else [Path.cwd().resolve()]

    if config_from_cli.get("config"):
        config["ini"] = Path(config_from_cli.pop("config"))
        config["root"] = config["ini"].parent
    else:
        config["root"], config["ini"] = _find_project_root_and_ini(config["paths"])
    config_from_file = _read_config(config["ini"]) if config["ini"] is not None else {}

    config["markers"] = {
        "depends_on": "Attach a dependency/dependencies to a task.",
        "produces": "Attach a product/products to a task.",
    }

    pm.hook.pytask_parse_config(
        config=config,
        config_from_cli=config_from_cli,
        config_from_file=config_from_file,
    )

    pm.hook.pytask_post_parse(config=config)

    return config


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    config_from_file["ignore"] = parse_value_or_multiline_option(
        config_from_file.get("ignore")
    )

    config["ignore"] = (
        get_first_not_none_value(
            config_from_cli,
            config_from_file,
            key="ignore",
            default=[],
            callback=to_list,
        )
        + IGNORED_FILES_AND_FOLDERS
    )

    config["debug_pytask"] = get_first_not_none_value(
        config_from_cli, config_from_file, key="debug_pytask", default=False
    )
    if config["debug_pytask"]:
        config["pm"].trace.root.setwriter(click.echo)
        config["pm"].enable_tracing()


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
    parent_directories = (
        common_ancestor.parents
        if common_ancestor.is_file()
        else [common_ancestor] + list(common_ancestor.parents)
    )
    for parent, config_name in itertools.product(
        parent_directories, ["pytask.ini", "tox.ini", "setup.cfg"]
    ):
        path = parent.joinpath(config_name)

        if path.exists():
            config = configparser.ConfigParser()
            config.read(path)
            if "pytask" in config.sections():
                config_path = path
                break

    if config_path is not None:
        root = config_path.parent
    else:
        root = common_ancestor if common_ancestor.is_dir() else common_ancestor.parent

    return root, config_path


def _read_config(path):
    config = configparser.ConfigParser()
    config.read(path)
    return dict(config["pytask"])


def _get_terminal_width() -> int:
    """Get the window width of the terminal."""
    width, _ = shutil.get_terminal_size(fallback=(80, 24))

    # The Windows get_terminal_size may be bogus, let's sanitize a bit.
    if width < 40:
        width = 80

    # Delete one character which prevents accidental line breaks.
    width -= 1

    return width
