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
		self.map_name = map_name
		super(MapExists, self).__init__(**kwargs)

	def __repr__(self):
		log.error("Map with name {} already exists.".format(self.map_name))


class LayoutExists(FileExistsError):
	"""
		Raised when a layout (in Pro only) already exists because a new one cannot be added with the same name
	"""
	def __init__(self, layout_name, **kwargs):
		self.layout_name = layout_name
		super(LayoutExists, self).__init__(**kwargs)

	def __repr__(self):
		log.error("Layout with name {} already exists.".format(self.layout_name))

class _AmaptorNotFoundError(FileNotFoundError):
	"""
		Raised when a process is trying to find a specific layout (Pro only) and it is not found.
	"""
	def __init__(self, name, extra_text=None, **kwargs):
		self.item_name = name
		self.extra_text = extra_text
		super(_AmaptorNotFoundError, self).__init__(**kwargs)

	def __repr__(self):
		log.error("{} with name {} does not exist. {}".format(self.type, self.item_name, self.extra_text))

class MapNotFoundError(_AmaptorNotFoundError):
	"""
		Raised when a process is trying to find a specific map and it is not found.
	"""
	def __init__(self, *args, **kwargs):
		self.type = "Map"
		super(MapNotFoundError, self).__init__(*args, **kwargs)

class LayoutNotFoundError(_AmaptorNotFoundError):
	"""
		Raised when a process is trying to find a specific layout (Pro only) and it is not found.
	"""
	def __init__(self, *args, **kwargs):
		self.type = "Layout"
		super(LayoutNotFoundError, self).__init__(*args, **kwargs)

class MapFrameNotFoundError(_AmaptorNotFoundError):
	"""
		Raised when a process is trying to find a specific layout (Pro only) and it is not found.
	"""
	def __init__(self, *args, **kwargs):
		self.type = "MapFrame"
		super(MapFrameNotFoundError, self).__init__(*args, **kwargs)

class ElementNotFoundError(_AmaptorNotFoundError):
	"""
		Raised when searching a layout for an element, and it's not found
	"""
	def __init__(self, *args, **kwargs):
		self.type = "Element"
		super(ElementNotFoundError, self).__init__(*args, **kwargs)

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
		self.description = description
		self.field = field
		super(EmptyFieldError, self).__init__(**kwargs)

	def __repr__(self):
		log.error("{} is empty or missing. {}".format(self.field, self.description))

class NotSupportedError(NotImplementedError):
	"""
		Raised when a feature is not supported by ArcGIS itself.
	"""
	def __init__(self, message, **kwargs):
		log.error("Not Supported: {}.".format(message))
		super(NotSupportedError, self).__init__(**kwargs)
	# for use when a specific mapping function not implemented