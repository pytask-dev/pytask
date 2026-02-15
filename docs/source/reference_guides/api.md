# API

!!! note "Migration status"

```
The Sphinx-based API pages were migrated to `mkdocstrings`. Some Sphinx-only
features (notably `autoprotocol` details and cross-reference backlinks) are not yet
fully equivalent in this stack.
```

## Command line interface

::: pytask.ColoredCommand ::: pytask.ColoredGroup ::: pytask.EnumChoice

## Compatibility

::: pytask.check_for_optional_program ::: pytask.import_optional_dependency

## Console

::: pytask.console

## Exceptions

::: pytask.PytaskError ::: pytask.CollectionError ::: pytask.ConfigurationError :::
pytask.ExecutionError ::: pytask.ResolvingDependenciesError :::
pytask.NodeNotCollectedError ::: pytask.NodeNotFoundError

## General classes

::: pytask.Session ::: pytask.DataCatalog

## Marks

Built-in marks are available on `pytask.mark`:

- `pytask.mark.persist`
- `pytask.mark.skipif`
- `pytask.mark.skip_ancestor_failed`
- `pytask.mark.skip_unchanged`
- `pytask.mark.skip`
- `pytask.mark.try_first`
- `pytask.mark.try_last`

### Mark classes

::: pytask.Mark ::: pytask.mark ::: pytask.MarkDecorator ::: pytask.MarkGenerator

### Mark utilities

::: pytask.get_all_marks ::: pytask.get_marks ::: pytask.has_mark :::
pytask.remove_marks ::: pytask.set_marks

## Protocols

::: pytask.PNode ::: pytask.PPathNode ::: pytask.PTask ::: pytask.PTaskWithPath :::
pytask.PProvisionalNode

## Nodes

::: pytask.PathNode ::: pytask.PickleNode ::: pytask.PythonNode ::: pytask.DirectoryNode
::: pytask.parse_dependencies_from_task_function :::
pytask.parse_products_from_task_function

## Tasks

::: pytask.task ::: pytask.Task ::: pytask.TaskWithoutPath ::: pytask.CollectionMetadata

## Outcomes

::: pytask.ExitCode ::: pytask.CollectionOutcome ::: pytask.TaskOutcome ::: pytask.Exit
::: pytask.Persisted ::: pytask.Skipped ::: pytask.SkippedAncestorFailed :::
pytask.SkippedUnchanged ::: pytask.count_outcomes

## Path utilities

::: pytask.path.import_path ::: pytask.path.hash_path

## Programmatic interfaces

::: pytask.build_dag ::: pytask.build

## Reports

::: pytask.CollectionReport ::: pytask.ExecutionReport ::: pytask.DagReport

## Tree utilities

::: pytask.tree_util.tree_flatten_with_path ::: pytask.tree_util.tree_leaves :::
pytask.tree_util.tree_map ::: pytask.tree_util.tree_map_with_path :::
pytask.tree_util.tree_structure

## Typing

::: pytask.Product ::: pytask.is_task_function

## Tracebacks

::: pytask.Traceback

## Warnings

::: pytask.WarningReport ::: pytask.parse_warning_filter :::
pytask.warning_record_to_str
