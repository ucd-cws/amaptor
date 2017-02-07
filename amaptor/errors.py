import logging
log = logging.getLogger("amaptor")

from amaptor.version_check import ARCMAP

if ARCMAP:
	FileExistsError = OSError  # define it for Python 2, basically raise an OSError in that case
	FileNotFoundError = OSError

class MapExists(FileExistsError):
	"""
		Raised when a map or data frame already exists because a new one cannot be added with the same name
	"""
	def __init__(self, map_name, **kwargs):
		log.error("Map with name {} already exists.".format(map_name))
		super(MapExists, self).__init__(**kwargs)


class LayoutExists(FileExistsError):
	"""
		Raised when a layout (in Pro only) already exists because a new one cannot be added with the same name
	"""
	def __init__(self, map_name, **kwargs):
		log.error("Layout with name {} already exists.".format(map_name))
		super(LayoutExists, self).__init__(**kwargs)


class MapNotFoundError(FileNotFoundError):
	"""
		Raised when a process is trying to find a specific map and it is not found.
	"""
	def __init__(self, map_name, **kwargs):
		log.error("Map with name {} does not exist.".format(map_name))
		super(MapNotFoundError, self).__init__(**kwargs)


class LayoutNotFoundError(FileNotFoundError):
	"""
		Raised when a process is trying to find a specific layout (Pro only) and it is not found.
	"""
	def __init__(self, layout_name, **kwargs):
		log.error("Layout with name {} does not exist.".format(layout_name))
		super(LayoutNotFoundError, self).__init__(**kwargs)


class MapNotImplementedError(NotImplementedError):
	"""
		Raised when a feature is only implemented for either ArcMap or ArcGIS Pro and code tries to use it in the environment
		it is not applicable to.
	"""
	def __init__(self, feature_name, arcmap_or_pro, **kwargs):
		log.error("Feature {} is not implemented for Arc {}.".format(feature_name, arcmap_or_pro))
		super(MapNotImplementedError, self).__init__(**kwargs)
	# for use when a specific mapping function not implemented


class LayerNotFoundError(ValueError):
	"""
		Raised when searching for a specific layer and it isn't found.
	"""
	pass  # for use when looking up layers


class EmptyFieldError(ValueError):
	def __init__(self, field, description, **kwargs):
		log.error("{} is empty or missing. {}".format(field, description))
		super(EmptyFieldError, self).__init__(**kwargs)