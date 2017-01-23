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

class LayerNotFoundError(ValueError):
	pass  # for use when looking up layers


class Map(object):
	"""
		Corresponds to an ArcMap Data Frame or an ArcGIS Pro Map
	"""
	def __init__(self, map_object, project):
		self._map_object = map_object
		self.project = project
		self.layers = []

		self.list_layers()

	def _get_layers_pro(self):
		self.layers = self._map_object.listLayers()

	def _get_layers_arcmap(self):
		self.layers = mapping.ListLayers(self.project.MapDocument)

	def list_layers(self):
		if PRO:
			self._get_layers_pro()
		else:
			self._get_layers_arcmap()

		return self.layers

	def insert_layer(self, reference_layer, insert_layer_or_layerfile, insert_position="BEFORE"):

		if PRO:
			self._map_object.insertLayer(reference_layer, insert_layer_or_layerfile=insert_layer_or_layerfile, insert_position=insert_position)
		else:
			mapping.InsertLayer(self._map_object, reference_layer, insert_layer_or_layerfile, insert_position)

		# update the internal layers list at the end
		self.list_layers()

	def insert_layer_by_name_or_path(self, insert_layer_or_layer_file, near_name=None, near_path=None, insert_position="BEFORE"):
		"""
			Not a standard arcpy.mapping or arcpy.mp function - given a name or data source path of a layer, finds it in the layers, and inserts it.
			Only provide either near_name or near_path. If both are provided, near_path will be used because it's more specifci
		:return: None
		"""

		reference_layer = self.find_layer(name=near_name, path=near_path)
		self.insert_layer(reference_layer=reference_layer, insert_layer_or_layerfile=insert_layer_or_layer_file, insert_position=insert_position)

	def find_layer(self, name=None, path=None):
		"""
			Given the name OR Path of a layer in the map, returns the layer object. If both are provided, returns based on path
		:param name:
		:param path:
		:return: arcpy.Layer object
		"""

		for layer in self.layers:
			if path is not None and layer.dataSource == path:
				return layer
			elif name is not None and layer.name == name:
				return layer


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
			Sets up the data based on the ArcGIS Pro Project. Only called if working with arcpy.mp and after any needed
			conversion from Map Document to Pro Project is done.
		:param path:
		:return:
		"""
		self.ArcGISProProject = mp.ArcGISProject(self.path)
		for l_map in self.ArcGISProProject.listMaps():
			self.maps.append(Map(l_map, self))

	def _arcmap_setup(self):
		"""
			Sets up data based on an ArcGIS Map Document. Only called if working with arcpy.mapping and after any
			needed conversion from Pro Project to map document is done (can we go that way?)
		:return:
		"""
		pass  # to implement when I switch my interpreter to ArcMap's so I can get autocomplete checking, etc
		# self.MapDocument = mapping.

	def list_maps(self):
		"""
			Provided to give a similar interface to ArcGIS Pro - Project.maps is also publically accessible
		:return:
		"""
		return self.maps



