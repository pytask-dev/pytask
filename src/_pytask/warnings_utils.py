from __future__ import annotations

import functools
import re
import textwrap
import warnings
from contextlib import contextmanager
from typing import cast
from typing import Generator
from typing import Tuple, TYPE_CHECKING

import attr
from _pytask.mark_utils import get_marks
from _pytask.nodes import Task
from _pytask.outcomes import Exit

if TYPE_CHECKING:
    from _pytask.session import Session


__all__ = [
    "catch_warnings_for_item",
    "parse_filterwarnings",
    "parse_warning_filter",
    "WarningReport",
]


@attr.s(kw_only=True)
class WarningReport:
    message = attr.ib(type=str)
    fs_location = attr.ib(type=Tuple[str, int])
    id_ = attr.ib(type=str)


@functools.lru_cache(maxsize=50)
def parse_warning_filter(
    arg: str, *, escape: bool
) -> tuple[warnings._ActionKind, str, type[Warning], str, int]:
    """Parse a warnings filter string.

    This is copied from warnings._setoption with the following changes:

    - Does not apply the filter.
    - Escaping is optional.
    - Raises UsageError so we get nice error messages on failure.

    """
    __tracebackhide__ = True
    error_template = textwrap.dedent(
        f"""\
        while parsing the following warning configuration:
          {arg}
        This error occurred:
        {{error}}
        """
    )

    parts = arg.split(":")
    if len(parts) > 5:
        doc_url = (
            "https://docs.python.org/3/library/warnings.html#describing-warning-filters"
        )
        error = textwrap.dedent(
            f"""\
            Too many fields ({len(parts)}), expected at most 5 separated by colons:
              action:message:category:module:line
            For more information please consult: {doc_url}
            """
        )
        raise Exit(error_template.format(error=error))

    while len(parts) < 5:
        parts.append("")
    action_, message, category_, module, lineno_ = (s.strip() for s in parts)
    try:
        action: warnings._ActionKind = warnings._getaction(action_)  # type: ignore
    except warnings._OptionError as e:
        raise Exit(error_template.format(error=str(e)))
    try:
        category: type[Warning] = _resolve_warning_category(category_)
    except Exit as e:
        raise Exit(str(e))
    if message and escape:
        message = re.escape(message)
    if module and escape:
        module = re.escape(module) + r"\Z"
    if lineno_:
        try:
            lineno = int(lineno_)
            if lineno < 0:
                raise ValueError("number is negative")
        except ValueError as e:
            raise Exit(error_template.format(error=f"invalid lineno {lineno_!r}: {e}"))
    else:
        lineno = 0
    return action, message, category, module, lineno


def _resolve_warning_category(category: str) -> type[Warning]:
    """Copied from warnings._getcategory, but changed so it lets exceptions (specially
    ImportErrors) propagate so we can get access to their tracebacks (#9218)."""
    __tracebackhide__ = True
    if not category:
        return Warning

    if "." not in category:
        import builtins as m

        klass = category
    else:
        module, _, klass = category.rpartition(".")
        m = __import__(module, None, None, [klass])
    cat = getattr(m, klass)
    if not issubclass(cat, Warning):
        raise Exception(f"{cat} is not a Warning subclass")
    return cast(type[Warning], cat)


def warning_record_to_str(warning_message: warnings.WarningMessage) -> str:
    """Convert a warnings.WarningMessage to a string."""
    msg = warnings.formatwarning(
        message=warning_message.message,
        category=warning_message.category,
        filename=warning_message.filename,
        lineno=warning_message.lineno,
        line=warning_message.line,
    )
    return msg


def parse_filterwarnings(x: str | list[str] | None) -> list[str]:
    """Parse filterwarnings."""
    if x is None:
        return []
    elif isinstance(x, str):
        return [i.strip() for i in x.split("\n")]
    elif isinstance(x, list):
        return [i.strip() for i in x]
    else:
        raise TypeError("'filterwarnings' must be a str, list[str] or None.")


@contextmanager
def catch_warnings_for_item(
    session: "Session",
    task: Task | None = None,
    when: str | None = None,
) -> Generator[None, None, None]:
    """Context manager that catches warnings generated in the contained execution block.

    ``item`` can be None if we are not in the context of an item execution. Each warning
    captured triggers the ``pytest_warning_recorded`` hook.

    """
    with warnings.catch_warnings(record=True) as log:
        # mypy can't infer that record=True means log is not None; help it.
        assert log is not None

        for arg in session.config["filterwarnings"]:
            warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        # apply filters from "filterwarnings" marks
        if task is not None:
            for mark in get_marks(task, "filterwarnings"):
                for arg in mark.args:
                    warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        yield

        if task is not None:
            id_ = task.short_name
        else:
            id_ = when

        for warning_message in log:
            fs_location = warning_message.filename, warning_message.lineno
            session.warnings.append(
                WarningReport(
                    message=warning_record_to_str(warning_message),
                    fs_location=fs_location,
                    id_=id_,
                )
            )
