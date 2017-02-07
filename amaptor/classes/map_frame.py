import logging
log = logging.getLogger("amaptor")

class MapFrame(object):
	def __init__(self, map_frame_object, layout):
		self._map_frame_object = map_frame_object
		self.layout = layout

	@property
	def name(self):
		return self._map_frame_object.name

	@name.setter
	def name(self, value):
		self._map_frame_object.name = value

	@property
	def map(self):
		return self._map_frame_object.map

	@map.setter
	def map(self, value):
		self._map_frame_object.map = value