import logging
log = logging.getLogger("amaptor")

import arcpy

from amaptor.version_check import PRO, ARCMAP, mapping, mp
from amaptor.errors import NotSupportedError, EmptyFieldError
from amaptor.functions import get_workspace_type

class Layer(object):
	"""
		This object is new, and existing code in amaptor hasn't yet been transitioned to using amaptor layers instead of
		native layers. Some amaptor functions *return* native layers, so care should be used when transitioning.
	"""
	def __init__(self, layer_object_or_file, name=None, map_object=None):
		"""
		:param layer_object_or_file: an actual instance of a layer object, or a layer file path
		:param name: used when loading from a file in Pro to select the layer of interest
		:param map: the map this layer belongs to - optional but used when updating symbology in ArcMap
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

		self.map = map_object

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

	@property
	def symbology(self):
		return self.layer_object.symbology

	@symbology.setter
	def symbology(self, symbology):
		"""
			Updates layer symbology based on copying from:
			 1) amaptor Layer object
			 2) arcpy.mapping/arcpy.mp Layer objects
			 3) symbology object. Symbology objects only exist in Pro, so take care when using them for cross-platform support.

			raises NotSupportedError if the provided object cannot be copied from. If you wish to copy symbology from a Layer
			file, open it and retrieve the appropriate Layer object and pass it here.

			IMPORTANT: If you are setting symbology using this method in ArcMap, you MUST attach an amaptor.Map instance
			 representing the Data Frame that this layer is within as this_layer.map. Example usage

			```
			  	# my_map is an amaptor.Map object instance
			  	my_layer = my_map.find_layer("layer_name")
			  	symbol_layer = my_map.find_layer("layer_with_symbology_to_copy")
			  	my_layer.map = my_map  # set the map attribute so it knows what data frame to use. Should be an amaptor.Map object, not an actual data frame.
			  	my_layer.symbology = symbol_layer # copies symbology from symbol_layer to my_layer
			```

		:param symbology: Symbology can be a symbology object or a layer to copy it from
		:return:
		"""
		if PRO:
			if isinstance(symbology, arcpy._mp.Symbology):
				new_symbology = symbology
			elif isinstance(symbology, arcpy._mp.Layer) or isinstance(symbology, Layer):  # if it's an amaptor layer, and we're Pro, copy it from there
				new_symbology = symbology.symbology
			else:
				raise NotSupportedError("Cannot retrieve symbology from the object provided. Accepted types are amaptor.Layer, arcpy.mp.Symbology, and arcpy.mp.Layer. You provided {}".format(type(symbology)))
			self.layer_object.symbology = new_symbology
		else:  # if ArcMap, we need to do some workaround

			from amaptor.classes.map import Map  # if we put this at the top, we get a circular import - need it to run at runtime for checking - this should be refactored, but not immediately sure how since these classes are mostly appropriately isolated, but bidrectionally reference each other
			if self.map is None or not isinstance(self.map, Map):
				raise EmptyFieldError("map", "Layer is not attached to an amaptor.Map instance - cannot change symbology. See documentation.")

			if isinstance(symbology, Layer):
				source_data = symbology.layer_object
			elif isinstance(symbology, arcpy.mapping.Layer):
				source_data = symbology
			else:
				raise NotSupportedError("Cannot retrieve symbology from the object provided. Accepted types are amaptor.Layer and arcpy.mapping.Layer. You provided {}".format(type(symbology)))

			arcpy.mapping.UpdateLayer(data_frame=self.map.map_object,
									  update_layer=self.layer_object,
									  source_layer=source_data,
									  symbology_only=True)

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