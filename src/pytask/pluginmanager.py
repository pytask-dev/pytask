import pluggy
from pytask import hookspecs


def get_plugin_manager():
    pm = pluggy.PluginManager("pytask")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("pytask")

    return pm


def register_default_plugins(pm):
    from pytask import cli
    from pytask import collect
    from pytask import config
    from pytask import debugging
    from pytask import execute
    from pytask import resolve_dependencies
    from pytask import skipping

    pm.register(cli)
    pm.register(collect)
    pm.register(config)
    pm.register(debugging)
    pm.register(execute)
    pm.register(resolve_dependencies)
    pm.register(skipping)
