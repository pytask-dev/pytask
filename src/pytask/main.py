import pdb
import sys

import attr
import pytask
from pytask.database import create_database
from pytask.enums import ExitCode
from pytask.exceptions import CollectionError
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


def main(config_from_cli):
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
        session.log_session_header()
        session.collect()
        session.resolve_dependencies()
        session.execute()

    except CollectionError:
        session.exit_code = ExitCode.COLLECTION_FAILED

    except ResolvingDependenciesError:
        session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

    except Exception as e:
        session.exit_code = ExitCode.FAILED
        if config["pdb"]:
            pdb.post_mortem()
        else:
            raise e

    return session


@attr.s
class Session:
    config = attr.ib()
    hook = attr.ib()
    collection_reports = attr.ib(default=[])
    tasks = attr.ib(default=[])
    resolving_dependencies_report = attr.ib(default=None)

    @classmethod
    def from_config(cls, config):
        return cls(config, config["pm"].hook)

    def log_session_header(self):
        self.hook.pytask_log_session_header(session=self)

    def collect(self):
        self.hook.pytask_collect(session=self)

    def resolve_dependencies(self):
        self.hook.pytask_resolve_dependencies(session=self)

    def execute(self):
        self.hook.pytask_execute(session=self)
