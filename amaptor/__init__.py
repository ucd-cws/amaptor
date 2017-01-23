from version import __version__
__name__ = "amaptor"

import logging
log = logging.getLogger("amaptor")

try:
	from arcpy import mapping
	DESKTOP = True
	PRO = False
	log.debug("Found ArcGIS Desktop (arcpy.mapping)")
except ImportError:
	try:
		from arcpy import mp
		DESKTOP = False
		PRO = True
		log.debug("Found ArcGIS Pro (arcpy.mp)")
	except ImportError:
		print("You must run {} on a Python installation that has arcpy installed".format(__name__))
		raise

