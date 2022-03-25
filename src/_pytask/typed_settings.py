from __future__ import annotations

from typing import Literal

import attrs
import click
from typed_settings.click_utils import DEFAULT_TYPES
from typed_settings.click_utils import TypeHandler


def handle_literal(_type, default):
    default_ = None if default is attrs.NOTHING else default
    return {"type": click.Choices(_type.__args__), "default": default_}


type_dict = {**DEFAULT_TYPES}


TYPE_HANDLER = TypeHandler(type_dict)
