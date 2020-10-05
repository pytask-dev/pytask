import pdb
import sys
import traceback

import click
from _pytask.config import hookimpl
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.shared import falsy_to_none_callback


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group):
    """Extend the command line interface."""
    cli.add_command(collect)


@hookimpl
def pytask_parse_config(config, config_from_cli):
    config["nodes"] = config_from_cli.get("nodes", False)


@click.command()
@click.argument(
    "paths", nargs=-1, type=click.Path(exists=True), callback=falsy_to_none_callback
)
@click.option("--nodes", is_flag=True)
@click.option(
    "--ignore",
    type=str,
    multiple=True,
    help=(
        "A pattern to ignore files or directories. For example, ``task_example.py`` or "
        "``src/*``."
    ),
    callback=falsy_to_none_callback,
)
@click.option(
    "-c", "--config", type=click.Path(exists=True), help="Path to configuration file."
)
def collect(**config_from_cli):
    """Collect tasks from paths."""
    config_from_cli["command"] = "collect"

    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)
        session = Session.from_config(config)

    except Exception:
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

        if config_from_cli.get("pdb"):
            traceback.print_exception(*sys.exc_info())
            pdb.post_mortem()

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)

            dictionary = _organize_tasks(session.tasks)
            _print_collected_tasks(dictionary, session.config)

            click.echo("\n" + "=" * config["terminal_width"])

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:
            traceback.print_exception(*sys.exc_info())
            if config["pdb"]:
                pdb.post_mortem()

            session.exit_code = ExitCode.FAILED

    sys.exit(session.exit_code)


def _organize_tasks(tasks):
    """Organize tasks in a dictionary.

    The dictionary has file names as keys and then a dictionary with task names and
    below a dictionary with dependencies and targets.

    """
    dictionary = {}
    for task in tasks:
        task_name = task.name.split("::")[1]
        dictionary[task.path] = dictionary.get(task.path, {})

        task_dict = {
            task_name: {
                "depends_on": [node.name for node in task.depends_on],
                "produces": [node.name for node in task.produces],
            }
        }

        dictionary[task.path].update(task_dict)

    return dictionary


def _print_collected_tasks(dictionary, config):
    click.echo("")

    for path in dictionary:
        click.echo(f"<Module {path}>")
        for task in dictionary[path]:
            click.echo(f"  <Function {task}>")
            if config["nodes"]:
                for dependency in dictionary[path][task]["depends_on"]:
                    click.echo(f"    <Dependency {dependency}>")

                for product in dictionary[path][task]["produces"]:
                    click.echo(f"    <Product {product}>")
