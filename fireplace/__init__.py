import pkg_resources
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

__author__ = "Jerome Leclanche"
__email__ = "jerome@leclan.ch"
__version__ = pkg_resources.require("fireplace")[0].version

from . import actions  # noqa
from . import aura  # noqa
from . import cards  # noqa
from . import deathknight  # noqa
from . import player  # noqa
from . import dsl  # noqa
from . import targeting  # noqa


if "FIREPLACE_NO_SETUPLOGGING" not in os.environ:
    from .logging import log

    # No need to call setup since it doesn't exist
    # log will be used for logging
