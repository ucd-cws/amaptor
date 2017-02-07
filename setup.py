from setuptools import setup
import os
import sys

try:
	import arcpy
except ImportError:
	ON_RTD = os.environ.get('READTHEDOCS', None) == 'True'
	if ON_RTD:  # if we're on read-the-docs, then we need to mock out arcpy, otherwise raise the exception
		class Mock(object):
			def __init__(self, *args, **kwargs):
				pass

			def __call__(self, *args, **kwargs):
				return Mock()

			@classmethod
			def __getattr__(cls, name):
				if name in ('__file__', '__path__'):
					return '/dev/null'
				elif name[0] == name[0].upper():
					mockType = type(name, (), {})
					mockType.__module__ = __name__
					return mockType
				else:
					return Mock()


		MOCK_MODULES = ['arcpy']
		for mod_name in MOCK_MODULES:
			sys.modules[mod_name] = Mock()
	else:
		raise

try:
	from amaptor.version import __version__, __author__
except RuntimeError:  # added so it can be installed with setup.py develop when signed in as an admin that's not signed into Portal in ArcGIS Pro
	__version__ = "0.1.0.1"
	__author__ = "nickrsan"

setup(name="amaptor",
	version=__version__,
	description="A compatibility layer (or adaptor) for mapping functions in ArcGIS 10.x (arcpy.mapping/Python 2) and"
				" ArcGIS Pro (arcpy.mp/Python 3)",
	long_description="""This library is an abstraction layer, with its own classes, to access mapping functions, regardless
	of which version of ArcGIS you are using. Think of it as the "six" package, but for arcpy.mapping/arcpy.mp. If you
	write your mapping code against this pacakge, it will work no matter which version of ArcGIS your end users are
	running. In general, the API adheres closely to the ArcGIS Pro api, since that has a cleaner, object-oriented design,
	but it may included differences. Further, methods are lowercased and underscored instead of camelcased, partially to
	make it easy to see at a glance that it's not the same code, and partially due to author preference.

	Documentation can be found at http://amaptor.readthedocs.io
	""",
	packages=['amaptor', 'amaptor.classes', ],
	package_data={"amaptor": [{"templates": ["*"]}]},
	install_requires=[],
	author=__author__,
	author_email="nrsantos@ucdavis.edu",
	url='https://github.com/ucd-cws/amaptor',
	include_package_data=True,
	)

