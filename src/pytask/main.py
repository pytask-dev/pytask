import pdb
import traceback

import attr
from pytask.database import create_database
from pytask.enums import ExitCode
from pytask.exceptions import CollectionError
from pytask.exceptions import ResolvingDependenciesError
from pytask.pluginmanager import get_plugin_manager
from pytask.pluginmanager import register_default_plugins


def main(config_from_cli):

    try:
        pm = get_plugin_manager()
        register_default_plugins(pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        create_database(**config["database"])

        session = Session.from_config(config)
        session.exit_code = ExitCode.OK

        session.collect()
        session.resolve_dependencies()
        session.execute()

    except CollectionError:
        session.exit_code = ExitCode.COLLECTION_FAILED

    except ResolvingDependenciesError:
        session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

    except Exception:
        session.exit_code = ExitCode.FAILED
        if config["pdb"]:
            pdb.post_mortem()
        else:
            traceback.print_exc()

    return session


@attr.s
class Session:
    config = attr.ib()
    hook = attr.ib()

    @classmethod
    def from_config(cls, config):
        return cls(config, config["pm"].hook)

    def collect(self):
        self.hook.pytask_collect(session=self)

    def resolve_dependencies(self):
        self.hook.pytask_resolve_dependencies(session=self)

    def execute(self):
        self.hook.pytask_execute(session=self)
