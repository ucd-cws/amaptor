import logging
log = logging.getLogger("amaptor")

import arcpy

from amaptor.classes.map_frame import MapFrame
from amaptor.version_check import PRO
from amaptor.errors import MapFrameNotFoundError, ElementNotFoundError, NotSupportedError

class Layout(object):
	"""
		Replicates Layouts so that we can do some nice things behind the scenes.

		In ArcMap, a single layout is created - that way, a layout can safely be retrieved for all documents and modifying
		properties of a layout modifies corresponding map document properties.
	"""

	def __init__(self, layout_object, project):
		self._layout_object = layout_object
		self.project = project
		self.frames = [MapFrame(frame, self) for frame in self._layout_object.listElements("MAPFRAME_ELEMENT")]  # frames connect back to maps, this connects to a project
		self.elements = self.list_elements()

	@property
	def name(self):
		"""
			Corresponds to the name of a layout in Pro and the Map Document's "title" property in ArcMap
		:return:
		"""
		if PRO:
			return self._layout_object.name
		else:
			return self.project.primary_document.title

	@name.setter
	def name(self, value):
		if PRO:
			self._layout_object.name = value
		else:
			self.project.primary_document.title = value

	def list_elements(self):
		self.elements = self._layout_object.listElements()
		return self.elements

	def export_to_png(self, out_path, resolution=300):
		"""
			Currently Pro only - needs refactoring to support ArcMap and Pro (should export map document in ArcMap).
			Also needs refactoring to combine Map and Layout export code.
		:param out_path:
		:param resolution:
		:return:
		"""
		self._layout_object.exportToPNG(out_path, resolution)

	def find_map_frame(self, name):
		"""
			Finds the map frame with a given name
		:param name: the name of the frame to find
		:return: MapFrame object
		"""

		if PRO:
			for frame in self.frames:
				if name == frame.name:
					return frame

			raise MapFrameNotFoundError(name=name)
		else:
			raise NotSupportedError("Map Frames are not supported in ArcMap")

	def find_element(self, name):
		"""
			Finds the first element matching the provided name
		:param name:
		:return:
		"""
		if PRO:
			for element in self.elements:
				if element.name == name:
					return element

			raise ElementNotFoundError(name)
		else:
			raise NotSupportedError("Element actions are not supported in ArcMap")

	def toggle_element(self, name_or_element, visibility="TOGGLE"):
		"""
			Given an element name, toggles, makes visible, or makes invisible that element.
		:param name_or_element: a string name of an element, or an element object
		:param visibility: Controls the action. Valid values are boolean (True, False) or the keyword "TOGGLE" which
			switches its current visibility state.
		:return:
		"""
		if PRO:
			if not isinstance(name_or_element, arcpy._mp.GraphicElement):
				element = self.find_element(name_or_element)
			else:
				element = name_or_element

			if visibility is True or visibility is False:
				element.visible = visibility
			elif visibility == "TOGGLE":
				if element.visible is True:
					element.visible = False
				else:
					element.visible = True
			else:
				raise ValueError("parameter visibility must be either a boolean value, (True, False) or the keyword \"TOGGLE\".")

	def export_to_pdf(self, out_path, **kwargs):
		self._layout_object.exportToPDF(out_path, **kwargs)

	def replace_text(self, text, replacement):
		"""
			Single layout analogue of Project.replace_text. Given a string and a replacement value, replaces all
			instances of that string in all text elements in the layout. Useful for having template strings in a map
			document
		:param text:
		:param replacement:
		:return:
		"""

		for elm in self._layout_object.listElements("TEXT_ELEMENT"):
			elm.text = elm.text.replace(text, replacement)
