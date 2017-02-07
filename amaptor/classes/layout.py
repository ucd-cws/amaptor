import logging
log = logging.getLogger("amaptor")

from amaptor.classes.map_frame import MapFrame

class Layout(object):
	"""
		Replicates Layouts so that we can do some nice things behind the scenes
	"""

	def __init__(self, layout_object, project):
		self._layout_object = layout_object
		self.frames = [MapFrame(frame, self) for frame in self._layout_object.listElements("MAPFRAME_ELEMENT")]  # frames connect back to maps, this connects to a project
		self.project = project

	@property
	def name(self):
		return self._layout_object.name

	@name.setter
	def name(self, value):
		self._layout_object.name = value