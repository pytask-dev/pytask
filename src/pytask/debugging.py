import click
import pytask
from pytask import _debugging
from pytask import _trace
from pytask.config import _get_first_not_none_value


@pytask.hookimpl
def pytask_add_parameters_to_cli(command):
    additional_parameters = [
        click.Option(["--pdb"], help="Enter debugger on errors.", is_flag=True),
        click.Option(["--trace"], help="Enter debugger at test start.", is_flag=True),
    ]
    command.params.extend(additional_parameters)


@pytask.hookimpl
def pytask_parse_config(config, config_from_cli):
    config["pdb"] = _get_first_not_none_value(config_from_cli, key="pdb", default=False)
    if config["pdb"]:
        config["pm"].register(_debugging)

    config["trace"] = _get_first_not_none_value(
        config_from_cli, key="trace", default=False
    )
    if config["trace"]:
        config["pm"].register(_trace)
