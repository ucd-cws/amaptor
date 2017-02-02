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

import arcpy

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

class MapExists(FileExistsError):
	def __init__(self, map_name, **kwargs):
		log.error("Map with name {} already exists.".format(map_name))
		super(MapExists, self).__init__(**kwargs)

class MapNotFoundError(FileExistsError):
	def __init__(self, map_name, **kwargs):
		log.error("Map with name {} does not exist.".format(map_name))
		super(MapNotFoundError, self).__init__(**kwargs)

class MapNotImplementedError(NotImplementedError):
	pass  # for use when a specific mapping function not implemented

class LayerNotFoundError(ValueError):
	pass  # for use when looking up layers

class EmptyFieldError(ValueError):
	def __init__(self, field, description, **kwargs):
		log.error("{} is empty or missing. {}".format(field, description))
		super(EmptyFieldError, self).__init__(**kwargs)

class Map(object):
	"""
		Corresponds to an ArcMap Data Frame or an ArcGIS Pro Map
	"""
	def __init__(self, project, map_object):

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

	def add_layer(self, add_layer, add_position="AUTO_ARRANGE"):
		"""
			Straight replication of addLayer API
		:param add_layer:
		:param add_position:
		:return:
		"""
		if PRO:
			self._map_object.addLayer(add_layer, add_position)
		else:
			arcpy.mapping.addLayer(self._map_object, add_layer, add_position)

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

	def insert_feature_class_with_symbology(self, feature_class, layer_file, layer_name=None, near_name=None, near_path=None, insert_position="BEFORE"):
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

		layer = make_layer_with_file_symbology(feature_class=feature_class, layer_file=layer_file, layer_name=layer_name)
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

	def to_package(self, output_file, **kwargs):
		"""
			Though it's not normally a mapping method, packaging concepts need translation between the two versions, so
			we've included to_package for maps and projects. In ArcGIS Pro, project.to_package will create a Project Package
			and map.to_package will create a map package. In ArcMap, both will create a map package. Calling to_package on the map
			will pass through all kwargs to map packaging because the signatures are the same between ArcMap and ArcGIS Pro.
			Sending kwargs to project.to_package will only send to project package since they differ.

		:param output_file:
		:param kwargs:
		:return:
		"""

		log.warning("Warning: Saving map to export package")
		self.save()

		if PRO:
			arcpy.PackageMap_management(self._map_object, output_file, **kwargs)
		else:
			arcpy.PackageMap_management(self.project.path, output_file, **kwargs)


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
			if path == "CURRENT":
				self.path = "CURRENT"  # will be redirected to actual path after setup
			elif path.endswith("aprx"):
				self.path = path
			elif path.endswith("mxd"):
				self.path = _import_mxd_to_new_pro_project(path)
			else:
				raise ValueError("Project or MXD path not recognized as an ArcGIS compatible file (.aprx or .mxd)")

			self._pro_setup()

		else:  # ArcMap

			if path == "CURRENT":
				self.path = "CURRENT"
				self._arcmap_setup()
			elif path.endswith("mxd"):
				self.path = path  # we'll overwrite once set up for "CURRENT"
				self._arcmap_setup()
			elif path.endswith("aprx"):
				# I need to find a way to create blank ArcGIS Pro projects here - may need to include one as a template to copy, but that seems silly/buggy.
				# planned approach is to create a Pro project in a temporary location, and import the map document provided.
				raise MapNotImplementedError("Support for Pro Projects in ArcMap is not possible. Please provide an MXD template to work with.")
			else:
				raise ValueError("Project or MXD path not recognized as an ArcGIS compatible file (.aprx or .mxd)")

		if path == "CURRENT":
			self.path = self._primary_document.filePath

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
			self.maps.append(Map(self, l_map))

	def _arcmap_setup(self):
		"""
			Sets up data based on an ArcGIS Map Document. Only called if working with arcpy.mapping and after any
			needed conversion from Pro Project to map docusment is done (can we go that way?)
		:return:
		"""
		self.map_document = mapping.MapDocument(self.path)
		self._primary_document = self.map_document
		for l_map in mapping.ListDataFrames(self.map_document):
			self.maps.append(Map(self, l_map))

	def list_maps(self):
		"""
			Provided to give a similar interface to ArcGIS Pro - Project.maps is also publically accessible
		:return:
		"""
		return self.maps

	def find_layer(self, path, find_all=True):
		"""
			Finds a layer in all maps by searching for the path. By default finds all, but can find just the first one too
		:param path:
		:param find_all:
		:return:
		"""
		layers = []
		for map in self.maps:
			try:
				new_layers = map.find_layer(path=path, find_all=find_all)
			except LayerNotFoundError:
				continue

			if find_all:  # if it didn't find any, we would have raised an exception, so we have something
				layers += new_layers
			else:  # if we were only supposed to get one, return it
				return new_layers

		if len(layers) == 0:
			raise LayerNotFoundError()

		return layers

	@property
	def active_map(self):
		return self.get_active_map()

	def find_map(self, name):
		"""
			Given a map name, returns the map object or raises
		:param name:
		:return:
		"""
		for l_map in self.maps:
			if l_map.map_object.name == name:
				return l_map
		else:
			raise MapNotFoundError(name)

	def check_map_name(self, name):
		"""
			Checks to see if the project already has a map with a given name. Since names must be unique, it is good to check
		:param name: name of map to check for
		:return: None. Raises an error if name is taken
		"""

		try:
			self.find_map(name)  # it finds one, then raise a MapExists error
			raise MapExists(name)
		except MapNotFoundError:
			pass  # it's great if it's not found

	def new_map(self, name, template_map=os.path.join(_TEMPLATES, "arcmap", "pro_import_map_template.mxd")):
		"""
			Creates a new map in the current project using a hack (importing a blank map document, and renaming data frame)
			Warning: Only works in Pro due to workaround.
		:param name: The name to give the imported map
		:param template_map: The map document to import. If we're just going with a blank new map, leave as default. To
							import some other template as your base, provide a path to a document importable to ArcGIS Pro'
							.importDocument function for projects.
		:return:
		"""

		if ARCMAP:
			raise MapNotImplementedError("ArcMap doesn't suppport adding data frames to map documents from Python")

		self.check_map_name(name)

		# step 1: import
		self._primary_document.importDocument(template_map)

		# step 2: set up for amaptor and rename to match passed value
		for l_map in self._primary_document.listMaps():
			if l_map.name == "_rename_template_amaptor":
				l_map.name = name
				new_map = Map(self, l_map)
				self.maps.append(new_map)

	def get_active_map(self, use_pro_backup=True):
		"""

		:param use_pro_backup: When True, it uses the first map in the ArcGIS Pro project, since Pro doesn't have a way
		 to get the active map.
		:return:
		"""
		if ARCMAP:
			for each_map in self.maps:
				if each_map._map_object.name == self._primary_document.activeDataFrame.name:
					return each_map
		else:
			# ArcGIS Pro doesn't have this capability, so we'll just use the first map (unfortunately).
			if use_pro_backup:
				return self.maps[0]
			else:
				raise NotImplementedError("ArcGIS Pro does not provide an interface to the active map")

	def save(self):
		self._primary_document.save()

	def save_a_copy(self, path):
		self._primary_document.saveACopy(path)

	def to_package(self, output_file, summary, tags, **kwargs):
		"""
			Though it's not normally a mapping method, packaging concepts need translation between the two versions, so
			we've included to_package for maps and projects. In ArcGIS Pro, project.to_package will create a Project Package
			and map.to_package will create a map package. In ArcMap, both will create a map package. Extra **kwargs beyond
			output path are only passed through to Pro Package command, not to map packages. To pass kwargs through to a map
			package, use a map object's to_package method.
		:param output_file:
		:param kwargs:
		:return:
		"""

		log.warning("Warning: Saving project to export package")
		self.save()

		if PRO:
			arcpy.PackageProject_management(self.path, output_file, summary=summary, tags=tags, **kwargs)
		else:
			arcpy.PackageMap_management(self.path, output_file, summary=summary, tags=tags)


def _import_mxd_to_new_pro_project(mxd, blank_pro_template=_PRO_BLANK_TEMPLATE, default_gdb="TEMP"):
	"""
		Handles importing an ArcMap Document into an ArcGIS Pro Project. Default Geodatabase is "TEMP" by default, indicating
		a temporary gdb should be created. It can also be "KEEP" to leave it alone, or it can be a path
	:param mxd:
	:param blank_pro_template:
	:param default_gdb:
	:return:
	"""

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

	if default_gdb != "KEEP":  # if we're supposed to modify it
		if default_gdb == "TEMP":
			new_default_gdb = tempfile.mktemp(prefix="amaptor_default_geodatabase", suffix=".gdb")
			arcpy.CreateFileGDB_management(os.path.split(new_default_gdb)[0], os.path.split(new_default_gdb)[1])
			project.defaultGeodatabase = new_default_gdb
		else:  # if it's not KEEP or TEMP it must be a path
			project.defaultGeodatabase = default_gdb

	project.save()

	# return the project path, setup will continue from here
	return new_temp_project


def make_layer_with_file_symbology(feature_class, layer_file, layer_name=None):
	"""
		Given a feature class and a template layer file with symbology, returns a new Layer object that has the layer
		from the layer file with the feature class as its data source. Optionally, layer can be renamed with layer_name
	:param feature_class:
	:param layer_file:
	:param layer_name:
	:return:
	"""
	layer = None
	if PRO:
		layer_file = mp.LayerFile(layer_file)
		for layer in layer_file.listLayers():
			break
	else:
		layer = mapping.Layer(layer_file)

	if layer is None:
		raise LayerNotFoundError("No layer available for copying from layer file")

	layer.dataSource = feature_class
	if layer_name:
		layer.name = layer_name

	return layer