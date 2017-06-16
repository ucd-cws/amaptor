import logging
log = logging.getLogger("amaptor")

from amaptor.classes.map_frame import MapFrame
from amaptor.version_check import PRO
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

	def export_to_png(self, out_path, resolution=300):
		"""
			Currently Pro only - needs refactoring to support ArcMap and Pro (should export map document in ArcMap).
			Also needs refactoring to combine Map and Layout export code.
		:param out_path:
		:param resolution:
		:return:
		"""
		self._layout_object.exportToPNG(out_path, resolution)

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
