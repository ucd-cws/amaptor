from .version import __version__

__name__ = "amaptor"

import logging
log = logging.getLogger("amaptor")

from amaptor.version_check import PRO, ARCMAP, MAP_EXTENSION, mapping, mp

from amaptor.errors import *  # I know it's bad practice. These will all be uniquely named (I know...)
from . import functions

from amaptor.classes.layer import Layer
from amaptor.classes.map_frame import MapFrame
from amaptor.classes.layout import Layout
from amaptor.classes.project import Project
from amaptor.classes.map import Map



