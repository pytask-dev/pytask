from _pytask.build import Build
from _pytask.capture import Capture
from _pytask.clean import Clean
from _pytask.collect_command import Collect
from _pytask.dag_command import Dag
from _pytask.debugging import Debugging
from _pytask.live import Live
from _pytask.logging import Logging
from _pytask.mark import Markers
from _pytask.parameters import Common
from _pytask.profile import Profile
from _pytask.warnings import Warnings

__all__ = ["Settings"]

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
