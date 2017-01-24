import os
import tempfile

from .version import __version__
__name__ = "amaptor"

import logging
log = logging.getLogger("amaptor")

# Only one of these will be true, but lets people test against the item of their choice (if amaptor.DESKTOP:, etc)
ARCMAP = None
PRO = None
MAP_EXTENSION = None

try:
	from arcpy import mapping
	ARCMAP = True
	PRO = False
	MAP_EXTENSION = "mxd"
	log.debug("Found ArcGIS Desktop (arcpy.mapping)")
except ImportError:
	try:
		from arcpy import mp
		ARCMAP = False
		PRO = True
		MAP_EXTENSION = "aprx"
		log.debug("Found ArcGIS Pro (arcpy.mp)")
	except ImportError:
		print("You must run {} on a Python installation that has arcpy installed".format(__name__))
		raise

_TEMPLATES = os.path.join(os.path.split(os.path.abspath(__file__))[0], "templates")
_PRO_BLANK_TEMPLATE = os.path.join(_TEMPLATES, "pro", "blank_pro_project", "blank_pro_project.aprx")

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
		self.layers = mapping.ListLayers(self.project.map_document)

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

	def insert_feature_class_with_symbology(self, feature_class, layer_file, near_name=None, near_path=None, insert_position="BEFORE"):
		"""
			Given a path to a feature calss, and a path to a layer file, creates a layer with layer file symbology and
			inserts it using insert_layer_by_name_or_path's approach
		:param feature_class:
		:param layer_file:
		:param near_name:
		:param near_path:
		:param insert_position:
		:return:
		"""

		layer = make_layer_with_file_symbology(feature_class=feature_class, layer_file=layer_file)
		self.insert_layer_by_name_or_path(layer, near_name=near_name, near_path=near_path, insert_position=insert_position)

	def find_layer(self, name=None, path=None, find_all=False):
		"""
			Given the name OR Path of a layer in the map, returns the layer object. If both are provided, returns based on path.
			If multiple layers with the same name/path exist, returns the first one, unless find_all is True - then it returns a list with all instances
		:param name:
		:param path:
		:return: arcpy.Layer object
		"""
		layers = []
		for layer in self.layers:
			if path is not None and layer.dataSource == path:
				if find_all:
					layers.append(layer)
				else:
					return layer
			elif name is not None and layer.name == name:
				if find_all:
					layers.append(layer)
				else:
					return layer

		if len(layers) == 0:  # basically, we should only be here if find_all is True and find_all came up empty
			raise LayerNotFoundError("Layer with provided name {} or path {} not found".format(name, path))

		return layers


class Project(object):
	"""
		An ArcGIS Pro Project or an ArcMap map document - maps in ArcGIS Pro and data frames in ArcMap are Map class attached to this project
		Access to the underlying object is provided using name ArcGISProProject and ArcMapDocument
	"""
	def __init__(self, path):

		self.maps = []  # stores list of included maps/dataframes
		self.path = None  # will be set after any conversion to current version of ArcGIS is done (aprx->mxd or vice versa)
		self.map_document = None
		self.arcgis_pro_project = None

		self._primary_document = None  # will be an alias for either self.map_document or self.arcgis_pro_project depending on what we're working with - makes it easier for items where API isn't different

		# this conditional tree is getting a little beefy now - could probably be refactored
		if PRO:
			if path.endswith("aprx"):
				self.path = path
			elif path.endswith("mxd"):
				self.path = _import_mxd_to_new_pro_project(path)
			else:
				raise ValueError("Project or MXD path not recognized as an ArcGIS compatible file (.aprx or .mxd)")

			self._pro_setup()
		else:  # ArcMap
			if path.endswith("mxd"):
				self.path = path
				self._arcmap_setup()
			elif path.endswith("aprx"):
				# I need to find a way to create blank ArcGIS Pro projects here - may need to include one as a template to copy, but that seems silly/buggy.
				# planned approach is to create a Pro project in a temporary location, and import the map document provided.
				raise MapNotImplementedError("Support for Pro Projects in ArcMap is not possible. Please provide an MXD template to work with.")
			else:
				raise ValueError("Project or MXD path not recognized as an ArcGIS compatible file (.aprx or .mxd)")

	def _pro_setup(self):
		"""
			Sets up the data based on the ArcGIS Pro Project. Only called if working with arcpy.mp and after any needed
			conversion from Map Document to Pro Project is done.
		:param path:
		:return:
		"""
		self.arcgis_pro_project = mp.ArcGISProject(self.path)
		self._primary_document = self.arcgis_pro_project
		for l_map in self.arcgis_pro_project.listMaps():
			self.maps.append(Map(l_map, self))

	def _arcmap_setup(self):
		"""
			Sets up data based on an ArcGIS Map Document. Only called if working with arcpy.mapping and after any
			needed conversion from Pro Project to map docusment is done (can we go that way?)
		:return:
		"""
		self.map_document = mapping.MapDocument(self.path)
		self._primary_document = self.map_document
		for l_map in mapping.ListDataFrames(self.map_document):
			self.maps.append(Map(l_map, self))

	def list_maps(self):
		"""
			Provided to give a similar interface to ArcGIS Pro - Project.maps is also publically accessible
		:return:
		"""
		return self.maps

	def save(self):
		self._primary_document.save()

	def save_a_copy(self, path):
		self._primary_document.saveACopy(path)


def _import_mxd_to_new_pro_project(mxd, blank_pro_template=_PRO_BLANK_TEMPLATE):
	log.warning("WARNING: Importing MXD to new Pro Project - if you call .save() it will not save back to original MXD. Use .save_a_copy('new_path') instead.")

	# can safely assume that if this is called, we're running on Pro and that's already been checked

	# copy blank project to new location - template is 1.3+
	blank_project = mp.ArcGISProject(blank_pro_template)
	new_temp_project = tempfile.mktemp(".aprx", "pro_project_import")
	blank_project.saveACopy(new_temp_project)
	del(blank_project)

	# strictly speaking, we don't need to destroy and recreate - should be able to edit original without saving - doing this just to keep things clear
	project = mp.ArcGISProject(new_temp_project)
	project.importDocument(mxd, include_layout=True)
	project.save()

	# return the project path, setup will continue from here
	return new_temp_project


def make_layer_with_file_symbology(feature_class, layer_file):
	if PRO:
		layer_file = mp.LayerFile(layer_file)
		for layer in layer_file.listLayers():
			break
	else:
		layer = mapping.Layer(layer_file)

	layer.dataSource = feature_class
	return layer