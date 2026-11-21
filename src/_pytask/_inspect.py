from __future__ import annotations

import ast
import builtins
import inspect
import sys
from inspect import get_annotations as _get_annotations_from_inspect
from types import ModuleType
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["get_annotations", "get_signature"]


def get_annotations(
    obj: Callable[..., Any],
    *,
    globals: dict[str, Any] | None = None,  # noqa: A002
    locals: dict[str, Any] | None = None,  # noqa: A002
    eval_str: bool = False,
) -> dict[str, Any]:
    """Return evaluated annotations with better support for deferred evaluation.

    Context
    -------
    * PEP 649 introduces deferred annotations which are only evaluated when explicitly
      requested. See https://peps.python.org/pep-0649/ for background and why locals can
      disappear between definition and evaluation time.
    * Python 3.14 ships `annotationlib` which exposes the raw annotation source and
      provides the building blocks we reuse here. The module doc explains the available
      formats: https://docs.python.org/3/library/annotationlib.html
    * Like Pydantic, we evaluate annotations with separate global and local
      namespaces and read signatures without evaluating annotations. See
      https://github.com/pydantic/pydantic/blob/v2.14.1/pydantic/_internal/_typing_extra.py
      and https://github.com/pydantic/pydantic/issues/12080.

    Rationale
    ---------
    When annotations refer to loop variables inside task generators, the locals that
    existed during decoration have vanished by the time pytask evaluates annotations
    while collecting tasks. Using
    [inspect.get_annotations](
    https://docs.python.org/3/library/inspect.html#inspect.get_annotations
    ) would therefore yield the same product path for every repeated task. By asking
    `annotationlib` for string representations and re-evaluating them with
    reconstructed locals (globals, default arguments, and the frame locals captured via
    [`@task`][pytask.task] at decoration time) we recover the correct per-task values.
    The frame locals capture is essential for
    cases where loop variables are only referenced in annotations (not in the function
    body or closure). On Python versions without `annotationlib`, we read the raw
    annotations with `inspect`, then evaluate them using the same namespace logic.
    """
    if not eval_str or not hasattr(obj, "__globals__"):
        return _get_annotations_from_inspect(
            obj, globals=globals, locals=locals, eval_str=eval_str
        )

    if sys.version_info < (3, 14):
        raw_annotations = _get_annotations_from_inspect(
            obj, globals=globals, locals=locals, eval_str=False
        )
    else:
        import annotationlib  # noqa: PLC0415

        raw_annotations = annotationlib.get_annotations(
            obj, globals=globals, locals=locals, format=annotationlib.Format.STRING
        )

    evaluation_globals = cast(
        "dict[str, Any]", obj.__globals__ if globals is None else globals
    )
    evaluation_locals = _build_evaluation_locals(obj, locals, evaluation_globals)

    evaluated_annotations = {}
    for name, expression in raw_annotations.items():
        evaluated_annotations[name] = _evaluate_annotation_expression(
            expression, evaluation_globals, evaluation_locals
        )

    return evaluated_annotations


def get_signature(obj: Callable[..., Any]) -> inspect.Signature:
    """Read a signature without evaluating annotations against unavailable locals.

    Pydantic's `signature_no_eval` uses the same version split. We request STRING
    instead of FORWARDREF on Python 3.14 so loop-local values are evaluated only
    when the collection namespace is available.
    """
    if sys.version_info >= (3, 14):
        import annotationlib  # noqa: PLC0415

        return inspect.signature(obj, annotation_format=annotationlib.Format.STRING)
    return inspect.signature(obj)


def _build_evaluation_locals(
    obj: Callable[..., Any],
    provided_locals: dict[str, Any] | None,
    evaluation_globals: dict[str, Any],
) -> dict[str, Any]:
    evaluation_builtins = evaluation_globals.get("__builtins__", builtins)
    if isinstance(evaluation_builtins, ModuleType):
        evaluation_builtins = vars(evaluation_builtins)

    # Recover missing names from defaults without shadowing globals or builtins.
    evaluation_locals = {
        name: value
        for name, value in _get_default_argument_locals(obj).items()
        if name not in evaluation_globals and name not in evaluation_builtins
    }
    if provided_locals:
        evaluation_locals.update(provided_locals)
    evaluation_locals.update(_get_snapshot_locals(obj))
    return evaluation_locals


def _get_snapshot_locals(obj: Callable[..., Any]) -> dict[str, Any]:
    metadata = getattr(obj, "pytask_meta", None)
    snapshot = getattr(metadata, "annotation_locals", None)
    return dict(snapshot) if snapshot else {}


def _get_default_argument_locals(obj: Callable[..., Any]) -> dict[str, Any]:
    try:
        parameters = get_signature(obj).parameters.values()
    except (TypeError, ValueError):
        return {}

    defaults = {}
    for parameter in parameters:
        if parameter.default is not inspect.Parameter.empty:
            defaults[parameter.name] = parameter.default
    return defaults


def _evaluate_annotation_expression(
    expression: Any, globals_: dict[str, Any] | None, locals_: dict[str, Any]
) -> Any:
    if not isinstance(expression, str):
        return expression
    evaluation_globals = globals_ if globals_ is not None else {}
    evaluated = eval(expression, evaluation_globals, locals_)  # noqa: S307
    if isinstance(evaluated, str):
        try:
            literal = ast.literal_eval(expression)
        except (SyntaxError, ValueError):
            return evaluated
        if isinstance(literal, str):
            try:
                return eval(literal, evaluation_globals, locals_)  # noqa: S307
            except Exception:  # noqa: BLE001
                return evaluated
    return evaluated
