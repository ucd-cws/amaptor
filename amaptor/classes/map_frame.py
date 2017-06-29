import logging
log = logging.getLogger("amaptor")

from amaptor.version_check import mp
from amaptor.errors import MapNotFoundError
#from amaptor.classes import map

class MapFrame(object):
	def __init__(self, map_frame_object, layout):
		self._map_frame_object = map_frame_object
		self.layout = layout

		try:
			self._map = layout.project.find_map(map_frame_object.map.name)  # find the map that this relates to
		except MapNotFoundError:
			self._map = None  # this is ok, because if we just created the frame, it may not be findable (as when we import a layout), but it should be set later

	def _set_map(self, amaptor_map):

		#if not isinstance(amaptor_map, map.Map):  # probably getting a circular import here, why it's commented out
		#	raise MapNotFoundError("Provided map is either None or not an instance of amaptor.classes.Map")

		self._map = amaptor_map
		self._map._index_frames()  # have it reindex all of the frames and maps it has
		self._map_frame_object.map = amaptor_map.map_object

	def set_extent(self, extent_object):
		self._map_frame_object.camera.setExtent(extent_object)

	def get_extent(self):
		return self._map_frame_object.camera.getExtent()

	@property
	def name(self):
		return self._map_frame_object.name

	@name.setter
	def name(self, value):
		self._map_frame_object.name = value

	@property
	def map(self):
		return self._map

	@map.setter
	def map(self, value):
		self._set_map(value)

