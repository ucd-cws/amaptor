import logging
log = logging.getLogger("amaptor")

# Only one of these will be true, but lets people test against the item of their choice (if amaptor.ARCMAP:, etc)
ARCMAP = None
PRO = None

MAP_EXTENSION = None

try:
	from arcpy import mapping
	ARCMAP = True
	PRO = False
	MAP_EXTENSION = "mxd"
	log.debug("Found ArcGIS Desktop (arcpy.mapping)")
	mp = None  # define so can always be imported
except ImportError:
	try:
		from arcpy import mp
		ARCMAP = False
		PRO = True
		MAP_EXTENSION = "aprx"
		log.debug("Found ArcGIS Pro (arcpy.mp)")
		mapping = None  # define so can always be imported
	except ImportError:
		print("You must run amaptor on a Python installation that has arcpy installed")
		raise