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
    from pytask import cli
    from pytask import collect
    from pytask import config
    from pytask import database
    from pytask import debugging
    from pytask import execute
    from pytask import logging
    from pytask import parametrize
    from pytask import resolve_dependencies
    from pytask import skipping

    pm.register(cli)
    pm.register(collect)
    pm.register(config)
    pm.register(database)
    pm.register(debugging)
    pm.register(execute)
    pm.register(logging)
    pm.register(parametrize)
    pm.register(resolve_dependencies)
    pm.register(skipping)


def main(kwargs):
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

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=kwargs)

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
    """The session of pytask.

    Attributes
    ----------
    config : dict
        A dictionary containing the configuration of the session
    hook : pluggy.hooks._HookRelay
        Hook holder object for performing 1:N hook calls where N is the number of
        registered hook implementations.
    collection_reports : List[pytask.report.CollectionReport], default None
        Reports collected while collecting tasks.
    tasks : List[pytask.nodes.MetaTask], default None
        Tasks collected
    resolving_dependencies_report : pytask.report.ResolvingDependenciesReport
    execution_reports : List[pytask.report.ExecutionReport], default None

    """

    config = attr.ib(type=dict)
    hook = attr.ib()
    collection_reports = attr.ib(default=None)
    tasks = attr.ib(default=None)
    resolving_dependencies_report = attr.ib(default=None)
    execution_reports = attr.ib(default=None)

    @classmethod
    def from_config(cls, config):
        """Construct the class from a config.

        Parameters
        ----------
        config : dict
            A dictionary with the parsed configuration.

        """
        return cls(config, config["pm"].hook)
