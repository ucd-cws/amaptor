import logging
log = logging.getLogger("amaptor")

import arcpy

from amaptor.version_check import PRO, ARCMAP, mapping, mp
from amaptor.errors import NotSupportedError
from amaptor.functions import get_workspace_type

class Layer(object):
	"""
		This object is new, and existing code in amaptor hasn't yet been transitioned to using amaptor layers instead of
		native layers. Some amaptor functions *return* native layers, so care should be used when transitioning.
	"""
	def __init__(self, layer_object_or_file, name=None):
		"""
		:param layer_object_or_file: an actual instance of a layer object, or a layer file path
		:param name: used when loading from a file in Pro to select the layer of interest
		"""
		self.layer_object = None

		if PRO and isinstance(layer_object_or_file, arcpy._mp.Layer):
			self.layer_object = layer_object_or_file
		elif ARCMAP and isinstance(layer_object_or_file, mapping.Layer):
			self.layer_object = layer_object_or_file
		elif PRO:  # otherwise, assume it's a path and run the import for each.
			layer_file = mp.LayerFile(layer_object_or_file)
			for layer in layer_file.listLayers():  # gets the specified layer from the layer file OR the last one
				self.layer_object = layer
				if name and layer.name == name:
					break
		else:
			self.layer_object = mapping.Layer(layer_object_or_file)

	@property
	def name(self):
		return self.layer_object.name

	@name.setter
	def name(self, value):
		self.layer_object.name = value

	@property
	def data_source(self):

		if not self.layer_object.supports("DATASOURCE"):
			raise NotSupportedError("Provided layer file doesn't support accessing or setting the data source")

		return self.layer_object.dataSource

	@data_source.setter
	def data_source(self, new_source):
		if not self.layer_object.supports("DATASOURCE"):
			raise NotSupportedError("Provided layer file doesn't support accessing or setting the data source")

		if PRO:
			self.layer_object.dataSource = new_source
		else:
			desc = arcpy.Describe(new_source)
			if desc.extension and desc.extension != "":  # get the name with extension for replacing the data source
				name = "{}.{}".format(desc.baseName, desc.extension)
			else:
				name = desc.baseName
			self.layer_object.replaceDataSource(desc.path, get_workspace_type(new_source), name)

	def __getter__(self, key):
		"""
			Helps this to be a standin where layers were used before because it will behave as expected for attributes
			of arcpy layers.
		:return:
		"""
		return getattr(self.layer_object, key)

	def __setter__(self, key, value):
		"""
			Helps this to be a standin where layers were used before because it will behave as expected for attributes
			of arcpy layers.
		:return:
		"""
		return setattr(self.layer_object, key, value)