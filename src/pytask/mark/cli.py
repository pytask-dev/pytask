import textwrap

import click
import pytask
from pytask import main
from pytask.enums import ExitCode
from pytask.main import Session
from pytask.pluginmanager import get_plugin_manager


@pytask.hookimpl
def pytask_add_parameters_to_cli(command: click.Command) -> None:
    command.params.append(
        click.Option(["--markers"], is_flag=True, help="Show available markers.")
    )


@pytask.hookimpl(tryfirst=True)
def pytask_main(config_from_cli: dict) -> int:
    if config_from_cli.get("markers", False):
        try:
            # Duplication of the same mechanism in :func:`pytask.main.pytask_main`.
            pm = get_plugin_manager()
            pm.register(main)
            pm.hook.pytask_add_hooks(pm=pm)

            config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

            session = Session.from_config(config)
            session.exit_code = ExitCode.OK

        except Exception as e:
            raise Exception("Error while configuring pytask.") from e

        for description in config["markers"].values():
            click.echo(
                textwrap.fill(
                    f"pytask.mark.{description}", width=config["terminal_width"]
                )
            )
            click.echo("")

        return session
