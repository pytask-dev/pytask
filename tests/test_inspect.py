from __future__ import annotations

from pathlib import Path
from typing import Annotated

from _pytask._inspect import get_annotations


def test_postponed_annotations_resolve_default_arguments_after_factory_returns():
    def factory():
        output = Path("out.txt")

        def example(output: Path = output) -> Annotated[str, output]:
            return str(output)

        return example

    annotations = get_annotations(factory(), eval_str=True)

    assert annotations == {"output": Path, "return": Annotated[str, Path("out.txt")]}


def test_explicit_annotation_namespaces_override_function_globals():
    def example(value: Path) -> Path:
        return value

    annotations = get_annotations(
        example, globals={"Path": int}, locals={"Path": str}, eval_str=True
    )

    assert annotations == {"value": str, "return": str}


def test_parameter_defaults_do_not_override_builtins():
    def example(str: str = "value") -> str:  # noqa: A002
        return str

    annotations = get_annotations(example, eval_str=True)

    assert annotations == {"str": str, "return": str}
