import pdb

import pytask.pluginmanager
from pytask import cli
from pytask.database import create_database
from pytask.enums import ExitCode
from pytask.exceptions import CollectionError
from pytask.exceptions import ExecutionError
from pytask.exceptions import ResolvingDependenciesError
from pytask.pluginmanager import get_plugin_manager
from pytask.session import Session


@pytask.hookimpl
def pytask_main(config_from_cli):
    """Run pytask.

    This is the main command to run pytask which usually receives kwargs from the
    command line interface. It can also be used to run pytask interactively. Pass
    configuration in a dictionary.

    Parameters
    ----------
    config_from_cli : dict
        A dictionary with options passed to pytask. In general, this dictionary holds
        the information passed via the command line interface.

    Returns
    -------
    session : pytask.session.Session
        The session captures all the information of the current run.

    """
    try:
        pm = get_plugin_manager()
        pm.register(cli)
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
