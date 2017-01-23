from version import __version__
__name__ = "amaptor"

import logging
log = logging.getLogger("amaptor")

# Only one of these will be true, but lets people test against the item of their choice (if amaptor.DESKTOP:, etc)
ARCMAP = None
PRO = None

try:
	from arcpy import mapping
	ARCMAP = True
	PRO = False
	log.debug("Found ArcGIS Desktop (arcpy.mapping)")
except ImportError:
	try:
		from arcpy import mp
		ARCMAP = False
		PRO = True
		log.debug("Found ArcGIS Pro (arcpy.mp)")
	except ImportError:
		print("You must run {} on a Python installation that has arcpy installed".format(__name__))
		raise


class MapNotImplementedError(NotImplementedError):
	pass  # for use when a specific mapping function not implemented


class Map(object):
	"""
		Corresponds to an ArcMap Data Frame or an ArcGIS Pro Map
	"""
	def __init__(self, map_object):
		self._map_object = map_object



class Project(object):
	"""
		An ArcGIS Pro Project or an ArcMap map document - maps in ArcGIS Pro and data frames in ArcMap are Map class attached to this project
		Access to the underlying object is provided using name ArcGISProProject and ArcMapDocument
	"""
	def __init__(self, path):

		self.maps = []  # stores list of included maps/dataframes
		self.path = None  # will be set after any conversion to current version of ArcGIS is done (aprx->mxd or vice versa)

		# this conditional tree is getting a little beefy now - could probably be refactored
		if PRO:
			if path.endswith("aprx"):
				self.path = path
				self._pro_setup()
			elif path.endswith("mxd"):
				raise MapNotImplementedError("Support for mxds in Pro is planned, but not implemented yet in amaptor")
			else:
				raise ValueError("Project or MXD path not recognized as an ArcGIS compatible file (.aprx or .mxd)")
		else:  # ArcMap
			if path.endswith("mxd"):
				self.path = path
				self._arcmap_setup()
			elif path.endswith("aprx"):
				# I need to find a way to create blank ArcGIS Pro projects here - may need to include one as a template to copy, but that seems silly/buggy.
				# planned approach is to create a Pro project in a temporary location, and import the map document provided.
				raise MapNotImplementedError("Support for Pro Projects (aprx) in ArcMap is planned, but not implemented yet in amaptor")
			else:
				raise ValueError("Project or MXD path not recognized as an ArcGIS compatible file (.aprx or .mxd)")

	def _pro_setup(self):
		"""
			Sets up the data based on the ArcGIS Pro Project
		:param path:
		:return:
		"""
		self.ArcGISProProject = mp.ArcGISProject(self.path)
		for l_map in self.ArcGISProProject.listMaps():
			self.maps.append(Map(l_map))

	def _arcmap_setup(self):
		pass  # to implement when I switch my interpreter to ArcMap's so I can get autocomplete checking, etc
		# self.MapDocument = mapping.

	def list_maps(self):
		"""
			Provided to give a similar interface to ArcGIS Pro - Project.maps is also publically accessible
		:return:
		"""
		return self.maps



