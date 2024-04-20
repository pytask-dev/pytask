from enum import Enum

from _pytask.capture_utils import CaptureMethod
from _pytask.capture_utils import ShowCapture
from _pytask.collect_command import Collect
from _pytask.dag_command import Dag
from _pytask.debugging import Debugging
from _pytask.live import Live
from _pytask.logging import Logging
from _pytask.parameters import Common
from _pytask.warnings import Warnings

__all__ = ["Build", "Capture", "Clean", "Markers", "Profile", "Settings"]

class Build:
    stop_after_first_failure: bool
    max_failures: float
    show_errors_immediately: bool
    show_traceback: bool
    dry_run: bool
    force: bool
    check_casing_of_paths: bool

class _ExportFormats(Enum):
    NO: str
    JSON: str
    CSV: str

class Profile:
    export: _ExportFormats

class _CleanMode(Enum):
    DRY_RUN: str
    FORCE: str
    INTERACTIVE: str

class Clean:
    directories: bool
    exclude: tuple[str, ...]
    mode: _CleanMode
    quiet: bool

class Markers:
    strict_markers: bool
    markers: dict[str, str]
    marker_expression: str
    expression: str

class Capture:
    capture: CaptureMethod
    s: bool
    show_capture: ShowCapture

class Settings:
    build: Build
    capture: Capture
    clean: Clean
    collect: Collect
    common: Common
    dag: Dag
    debugging: Debugging
    live: Live
    logging: Logging
    markers: Markers
    profile: Profile
    warnings: Warnings
