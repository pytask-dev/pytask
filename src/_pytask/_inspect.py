from __future__ import annotations

import ast
import inspect
import sys
from inspect import get_annotations as _get_annotations_from_inspect
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["get_annotations"]


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
    * Other projects run into the same constraints. Pydantic tracks their work in
      https://github.com/pydantic/pydantic/issues/12080; we might copy improvements from
      there once they settle on a stable strategy.

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
    body or closure). If any of these ingredients are missing—for example on Python
    versions without `annotationlib` - we fall back to the stdlib implementation,
    so behaviour on 3.10-3.13 remains unchanged.
    """
    if not eval_str or not hasattr(obj, "__globals__"):
        return _get_annotations_from_inspect(
            obj, globals=globals, locals=locals, eval_str=eval_str
        )

    if sys.version_info < (3, 14):
        raw_annotations = _get_annotations_from_inspect(
            obj, globals=globals, locals=locals, eval_str=False
        )
        evaluation_globals = cast(
            "dict[str, Any]", obj.__globals__ if globals is None else globals
        )
        evaluation_locals = evaluation_globals if locals is None else locals
        evaluated_annotations = {}
        for name, expression in raw_annotations.items():
            evaluated_annotations[name] = _evaluate_annotation_expression(
                expression, evaluation_globals, evaluation_locals
            )
        return evaluated_annotations

    import annotationlib  # noqa: PLC0415

    raw_annotations = annotationlib.get_annotations(
        obj, globals=globals, locals=locals, format=annotationlib.Format.STRING
    )

    evaluation_globals = obj.__globals__ if globals is None else globals
    evaluation_locals = _build_evaluation_locals(obj, locals)

    evaluated_annotations = {}
    for name, expression in raw_annotations.items():
        evaluated_annotations[name] = _evaluate_annotation_expression(
            expression, evaluation_globals, evaluation_locals
        )

    return evaluated_annotations


def _build_evaluation_locals(
    obj: Callable[..., Any], provided_locals: dict[str, Any] | None
) -> dict[str, Any]:
    # Order matters: later updates override earlier ones.
    # Default arguments are lowest priority (fallbacks), then provided_locals,
    # then snapshot_locals (captured loop variables) have highest priority.
    evaluation_locals: dict[str, Any] = {}
    evaluation_locals.update(_get_default_argument_locals(obj))
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
        parameters = inspect.signature(obj).parameters.values()
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
