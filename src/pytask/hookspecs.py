import click
import pluggy


hookspec = pluggy.HookspecMarker("pytask")


@hookspec
def pytask_add_hooks(pm):
    """Add hooks to the pluginmanager."""


# Hooks for the command-line interface.


@hookspec
def pytask_add_parameters_to_cli(command: click.Command):
    """Add parameter to :class:`click.Command`."""


# Hooks for the configuration.


@hookspec(firstresult=True)
def pytask_configure(pm, config_from_cli):
    """Configure pytask."""


@hookspec
def pytask_parse_config(config, config_from_cli, config_from_file):
    """Parse configuration from the CLI or from file."""


@hookspec
def pytask_post_parse(config):
    """Post parsing."""


# Hooks for the collection.


@hookspec(firstresult=True)
def pytask_collect(session):
    """Collect tasks from paths."""


@hookspec(firstresult=True)
def pytask_ignore_collect(path, config):
    """Ignore collected path."""


@hookspec(firstresult=True)
def pytask_collect_log(reports, tasks, config):
    """Log errors during the collection."""


@hookspec
def pytask_collect_modify_tasks(tasks, config):
    """Modify tasks after they have been collected for filtering, re-ordering, etc..

    Resource: https://github.com/pytest-dev/pytest/blob/master/src/_pytest/main.py#L326

    """


@hookspec(firstresult=True)
def pytask_collect_file_protocol(session, path, reports):
    """Start protocol to collect files."""


@hookspec(firstresult=True)
def pytask_collect_file(session, path, reports):
    """Collect tasks from files."""


@hookspec(firstresult=True)
def pytask_generate_tasks(session, name, obj):
    """Generate multiple tasks from name and object with parametrization."""


@hookspec(firstresult=True)
def generate_product_of_names_and_functions(
    session, name, obj, base_arg_names, arg_names, arg_values
):
    """Generate names and functions from Cartesian product."""


@hookspec
def pytask_generate_tasks_add_marker(obj, kwargs):
    """Add some keyword arguments as markers to task."""


@hookspec(firstresult=True)
def pytask_collect_task_protocol(session, reports, path, name, obj):
    """Start protocol to collect tasks."""


@hookspec
def pytask_collect_task_setup(session, reports, path, name, obj):
    """Steps before collecting a task."""


@hookspec(firstresult=True)
def pytask_collect_task(session, path, name, obj):
    """Collect a single task."""


@hookspec(firstresult=True)
def pytask_collect_node(path, node):
    """Collect a single node which is a dependency or a product."""


# Hooks for resolving dependencies.


@hookspec(firstresult=True)
def pytask_resolve_dependencies(session):
    """Resolve dependencies."""


@hookspec(firstresult=True)
def pytask_resolve_dependencies_create_dag(tasks):
    """Create the dag."""


@hookspec(firstresult=True)
def pytask_resolve_dependencies_select_execution_dag(dag):
    """Select the subgraph which needs to be executed."""


@hookspec(firstresult=True)
def pytask_resolve_dependencies_validate_dag(dag):
    """Validate the dag."""


@hookspec
def pytask_resolve_dependencies_log(session, report):
    """Log errors during resolving dependencies."""


# Hooks for running tasks.


@hookspec(firstresult=True)
def pytask_execute(session):
    """Loop over all tasks for the execution."""


@hookspec
def pytask_execute_log_start(session):
    """Start logging of execution."""


@hookspec(firstresult=True)
def pytask_execute_create_scheduler(session):
    """Create a scheduler for the execution."""


@hookspec(firstresult=True)
def pytask_execute_build(session):
    """Execute the build."""


@hookspec(firstresult=True)
def pytask_execute_task_protocol(session, task):
    """Run the protocol for executing a test."""


@hookspec
def pytask_execute_task_log_start(session, task):
    """Start logging of task execution."""


@hookspec
def pytask_execute_task_setup(session, task):
    """Set up the task execution."""


@hookspec(firstresult=True)
def pytask_execute_task(session, task):
    """ called to execute the task `item`."""


@hookspec
def pytask_execute_task_teardown(session, task):
    """Tear down task execution."""


@hookspec(firstresult=True)
def pytask_execute_task_process_report(session, report):
    """Process the report of a task."""


@hookspec(firstresult=True)
def pytask_execute_task_log_end(session, task, report):
    """End logging of task execution."""


@hookspec
def pytask_execute_log_end(session, reports):
    """End logging execution."""


# Hooks for general logging.


@hookspec
def pytask_log_session_header(session):
    """Log session information at the begin of a run."""
