import pdb
import sys

import attr
import pytask
from pytask.database import create_database
from pytask.enums import ExitCode
from pytask.exceptions import CollectionError
from pytask.exceptions import ExecutionError
from pytask.exceptions import ResolvingDependenciesError
from pytask.pluginmanager import get_plugin_manager


@pytask.hookimpl
def pytask_add_hooks(pm):
    from pytask import collect
    from pytask import config
    from pytask import database
    from pytask import debugging
    from pytask import execute
    from pytask import logging
    from pytask import parametrize
    from pytask import resolve_dependencies
    from pytask import skipping
    from pytask.mark import config as mark_config

    pm.register(collect)
    pm.register(config)
    pm.register(database)
    pm.register(debugging)
    pm.register(execute)
    pm.register(logging)
    pm.register(parametrize)
    pm.register(resolve_dependencies)
    pm.register(skipping)
    pm.register(mark_config)


@pytask.hookimpl
def pytask_main(config_from_cli):
    """Run pytask.

    This is the main command to run pytask which usually receives kwargs from the
    command line interface. It can also be used to run pytask interactively. Pass
    configuration in a dictionary.

    Parameters
    ----------
    kwargs : dict
        A dictionary with options passed to pytask. In general, this dictionary holds
        the information passed via the command line interface.

    Returns
    -------
    session : pytask.main.Session
        The session captures all the information of the current run.

    """
    try:
        pm = get_plugin_manager()
        pm.register(sys.modules[__name__])
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        create_database(**config["database"])

        session = Session.from_config(config)
        session.exit_code = ExitCode.OK

    except Exception as e:
        raise Exception("Error while configuring pytask.") from e

    try:
        session.hook.pytask_log_session_header(session=session)
        session.hook.pytask_collect(session=session)
        session.hook.pytask_resolve_dependencies(session=session)
        session.hook.pytask_execute(session=session)

    except CollectionError:
        session.exit_code = ExitCode.COLLECTION_FAILED

    except ResolvingDependenciesError:
        session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

    except ExecutionError:
        session.exit_code = ExitCode.FAILED

    except Exception as e:
        if config["pdb"]:
            pdb.post_mortem()
        else:
            raise e

    return session


@attr.s
class Session:
    """The session of pytask."""

    config = attr.ib(type=dict)
    """dict: A dictionary containing the configuration of the session."""

    hook = attr.ib()
    """pluggy.hooks._HookRelay: Holds all hooks collected by pytask."""

    collection_reports = attr.ib(default=None)
    """Optional[List[pytask.report.ExecutionReport]]: Reports for collected items.

    The reports capture errors which happened while collecting tasks.

    """

    tasks = attr.ib(default=None)
    """Optional[List[pytask.nodes.MetaTask]]: List of collected tasks."""

    resolving_dependencies_report = attr.ib(default=None)
    """Optional[pytask.report.ResolvingDependenciesReport]: A report.

    Report when resolving dependencies failed.

    """

    execution_reports = attr.ib(default=None)
    """Optional[List[pytask.report.ExecutionReport]]: Reports for executed tasks."""

    @classmethod
    def from_config(cls, config):
        """Construct the class from a config."""
        return cls(config, config["pm"].hook)
