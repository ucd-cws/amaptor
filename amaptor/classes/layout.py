import logging
log = logging.getLogger("amaptor")

from amaptor.classes.map_frame import MapFrame

class Layout(object):
	"""
		Replicates Layouts so that we can do some nice things behind the scenes
	"""

	def __init__(self, layout_object, project):
		self._layout_object = layout_object
		self.project = project
		self.frames = [MapFrame(frame, self) for frame in self._layout_object.listElements("MAPFRAME_ELEMENT")]  # frames connect back to maps, this connects to a project

	@property
	def name(self):
		return self._layout_object.name

	@name.setter
	def name(self, value):
		self._layout_object.name = value

	def export_to_png(self, out_path, resolution=300):
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
