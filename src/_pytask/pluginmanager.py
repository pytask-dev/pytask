import pluggy
from _pytask import hookspecs


def get_plugin_manager():
    pm = pluggy.PluginManager("pytask")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("pytask")

    return pm
