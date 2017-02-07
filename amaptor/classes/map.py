import logging
log = logging.getLogger("amaptor")

import arcpy

from amaptor.version_check import PRO, mapping, mp
from amaptor.errors import *
from amaptor.functions import reproject_extent, log
from amaptor.functions import make_layer_with_file_symbology, reproject_extent


class Map(object):
	"""
		Corresponds to an ArcMap Data Frame or an ArcGIS Pro Map
	"""
	def __init__(self, project, map_object):

		self.map_object = map_object
		self.project = project
		self.layers = []

		self.list_layers()

		self.frames = []
		self.layouts = []

	@property
	def name(self):
		return self.map_object.name

	@name.setter
	def name(self, value):
		self.map_object.name = value

	def _index_frames(self):
		for layout in self.project.layouts:
			for frame in layout.frames:
				if frame.map.name == self.name:
					self.frames.append(frame)
					if layout not in self.layouts:
						self.layouts.append(layout)


	def _get_layers_pro(self):
		self.layers = self.map_object.listLayers()

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
			self.map_object.addLayer(add_layer, add_position)
		else:
			arcpy.mapping.addLayer(self.map_object, add_layer, add_position)

		self.layers.append(add_layer)

	def insert_layer(self, reference_layer, insert_layer_or_layerfile, insert_position="BEFORE"):

		if PRO:
			self.map_object.insertLayer(reference_layer, insert_layer_or_layerfile=insert_layer_or_layerfile, insert_position=insert_position)
		else:
			mapping.InsertLayer(self.map_object, reference_layer, insert_layer_or_layerfile, insert_position)

		# update the internal layers list at the end
		self.list_layers()

	def set_extent(self, extent_object, set_frame="ALL", add_buffer=True):
		"""
			Sets map frames to a provided extent object. In ArcMap, just sets the data frame's extent. In Pro, it has many
			potential behaviors. If set_frame == "ALL" it sets all map frames linked to this map to this extent (default
			behavior) and sets the default camera for this map so that future map frames will use the same extent.
			If set_frame is an arcpy.mp MapFrame object instance, then it only sets the extent on that map frame.
		:param extent_object:
		:param set_frame: ignored in arcmap, behavior described in main method description.
		:param add_buffer: adds an empty space of 5% of the distance across the feature class around the provided exetent
		:return:
		"""

		if add_buffer:
			x_buf = (extent_object.XMax - extent_object.XMin) * .05
			y_buf = (extent_object.YMax - extent_object.YMin) * .05

			extent_object.XMax += x_buf
			extent_object.XMin -= x_buf
			extent_object.YMax += y_buf
			extent_object.YMin -= y_buf

		if PRO:
			if set_frame == "ALL":
				for frame in self.frames:
					extent = reproject_extent(extent_object, frame.camera.getExtent())
					frame.camera.setExtent(extent)
					self.map_object.defaultCamera.setExtent(extent)
			elif isinstance(set_frame, arcpy._mp.MapFrame):
				extent = reproject_extent(extent_object, set_frame.camera.getExtent())
				set_frame.camera.setExtent(extent)
			else:
				raise ValueError("Invalid parameter set_frame. It can either be \"ALL\" or an instance of an arcpy.mp MapFrame object")
		else:
			self.map_object.extent = reproject_extent(extent_object, self.map_object.extent)

	def zoom_to_layer(self, layer, set_layout="ALL"):
		"""
			Given a name of a layer as a string or a layer object, zooms the map extent to that layer
			WARNING: In Pro, see the parameter information for set_layout on the set_extent method for a description
			of how this option behaves.
		:param layer: can be a string name of a layer, or a layer object
		:return:
		"""
		if PRO:
			if not isinstance(layer, arcpy._mp.Layer):
				layer = self.find_layer(name=layer)
			self.set_extent(arcpy.Describe(layer.dataSource).extent)
		else:
			if not isinstance(layer, arcpy._mapping.Layer):
				layer = self.find_layer(name=layer)
			self.set_extent(layer.getExtent())
			arcpy.RefreshActiveView()

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
			arcpy.PackageMap_management(self.map_object, output_file, **kwargs)
		else:
			arcpy.PackageMap_management(self.project.path, output_file, **kwargs)