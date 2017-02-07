import os
import logging
log = logging.getLogger("amaptor")

import arcpy

from amaptor.version_check import PRO, ARCMAP, mapping, mp
from amaptor.classes.map import Map
from amaptor.classes.layout import Layout
from amaptor.classes.map_frame import MapFrame

from amaptor.constants import _TEMPLATES, _PRO_BLANK_LAYOUT
from amaptor.functions import _import_mxd_to_new_pro_project

from amaptor.errors import *


class Project(object):
	"""
		An ArcGIS Pro Project or an ArcMap map document - maps in ArcGIS Pro and data frames in ArcMap are Map class attached to this project
		Access to the underlying object is provided using name ArcGISProProject and ArcMapDocument
	"""

	def __init__(self, path):

		self.maps = []  # stores list of included maps/dataframes
		self.layouts = []
		self.path = None  # will be set after any conversion to current version of ArcGIS is done (aprx->mxd or vice versa)
		self.map_document = None
		self.arcgis_pro_project = None

		self.primary_document = None  # will be an alias for either self.map_document or self.arcgis_pro_project depending on what we're working with - makes it easier for items where API isn't different

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
			self.path = self.primary_document.filePath

	def _pro_setup(self):
		"""
			Sets up the data based on the ArcGIS Pro Project. Only called if working with arcpy.mp and after any needed
			conversion from Map Document to Pro Project is done.
		:param path:
		:return:
		"""
		self.arcgis_pro_project = mp.ArcGISProject(self.path)
		self.primary_document = self.arcgis_pro_project
		for l_map in self.arcgis_pro_project.listMaps():
			self.maps.append(Map(self, l_map))

		for layout in self.primary_document.listLayouts():
			self.layouts.append(Layout(layout, self))

		for map in self.maps:
			map._index_frames()

	def _arcmap_setup(self):
		"""
			Sets up data based on an ArcGIS Map Document. Only called if working with arcpy.mapping and after any
			needed conversion from Pro Project to map docusment is done (can we go that way?)
		:return:
		"""
		self.map_document = mapping.MapDocument(self.path)
		self.primary_document = self.map_document
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
		"""
			Returns the active map object or data frame as determined by get_active_map()
		:return:
		"""
		return self.get_active_map()

	def find_map(self, name):
		"""
			Given a map name, returns the map object or raises MapNotFoundError
		:param name:
		:return:
		"""
		for l_map in self.maps:
			if l_map.name == name:
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

	def new_map(self, name, template_map=os.path.join(_TEMPLATES, "arcmap", "pro_import_map_template.mxd"), template_df_name="_rename_template_amaptor"):
		"""
			Creates a new map in the current project using a hack (importing a blank map document, and renaming data frame)
			Warning: Only works in Pro due to workaround.
		:param name: The name to give the imported map
		:param template_map: The map document to import. If we're just going with a blank new map, leave as default. To
							import some other template as your base, provide a path to a document importable to ArcGIS Pro'
							.importDocument function for projects.
		:param template_df_name: The current name of the imported map document for renaming. Only needs to be set if template_map is overridden
		:return: amaptor.Map instance - also added to the map document, but returned for immediate use.
		"""

		if ARCMAP:
			raise MapNotImplementedError("ArcMap doesn't suppport adding data frames to map documents from Python")

		self.check_map_name(name)

		# step 1: import
		self.primary_document.importDocument(template_map)

		# step 2: set up for amaptor and rename to match passed value
		for l_map in self.primary_document.listMaps():
			if l_map.name == template_df_name:
				l_map.name = name
				new_map = Map(self, l_map)
				self.maps.append(new_map)
				return new_map

	def check_layout_name(self, name):
		try:
			self.find_layout(name)  # it finds one, then raise a MapExists error
			raise LayoutExists(name)
		except LayoutNotFoundError:
			pass  # it's great if it's not found

	def find_layout(self, name):
		"""
			PRO ONLY. Given a layout name, returns the amaptor.Layout object or raises LayoutNotFoundError
		:param name:
		:return:
		"""
		for layout in self.layouts:
			if layout.name == name:
				return layout
		else:
			raise LayoutNotFoundError(name)

	def new_layout(self, name, template_layout=_PRO_BLANK_LAYOUT, template_name="_pro_blank_layout_template"):
		"""
			PRO ONLY. Adds a new layout to an ArcGIS Pro Project by importing a saved blank layout. Alternatively,
			 you can provide an importable layout document (.pagx) for ArcGIS Pro, and then provide that layout's name
			 as template_name so that it can be renamed, and the provided template will be used instead of a blank.
		:param name:
		:param template_layout:
		:param template_name:
		:return:
		"""
		if ARCMAP:
			raise MapNotImplementedError("ArcMap doesn't suppport adding data frames to map documents from Python")

		# step 1: import
		self.primary_document.importDocument(template_layout)

		# step 2: set up for amaptor and rename to match passed value
		for layout in self.primary_document.listLayouts():
			if layout.name == template_name:
				layout.name = name
				new_layout = Layout(layout, self)
				self.layouts.append(new_layout)
				return new_layout

	def get_active_map(self, use_pro_backup=True):
		"""

		:param use_pro_backup: When True, it uses the first map in the ArcGIS Pro project, since Pro doesn't have a way
		 to get the active map.
		:return:
		"""
		if ARCMAP:
			for each_map in self.maps:
				if each_map.name == self.primary_document.activeDataFrame.name:
					return each_map
		else:
			# ArcGIS Pro doesn't have this capability, so we'll just use the first map (unfortunately).
			if use_pro_backup:
				return self.maps[0]
			else:
				raise NotImplementedError("ArcGIS Pro does not provide an interface to the active map")

	def save(self):
		"""
			Saves the project or map document in place.
		:return:
		"""
		self.primary_document.save()

	def save_a_copy(self, path):
		"""
			Saves the project or map document to the provided path.
		:param path:
		:return:
		"""
		self.primary_document.saveACopy(path)

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