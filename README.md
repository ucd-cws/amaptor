# Amaptor - Arcpy mapping compatibility layer
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/060aec7923304e209e5d14a676731572/badge.svg)](https://www.quantifiedcode.com/app/project/060aec7923304e209e5d14a676731572)

The goal of Amaptor is to be a _map adaptor_ - providing a single interface
for most mapping needs that works against both arcpy.mapping (ArcMap 10.x/Python 2.7)
and arcpy.mp (ArcGIS Pro/Python 3.4+). Think of it as being like the "six" library of ArcGIS mapping.

arcpy.mapping and arcpy.mp are separated for _good reason_ - the concepts behind
map documents/projects changed between ArcMap and ArcGIS Pro, so amaptor, as currently
conceptualized isn't meant to guarantee complete functionality in both cases, but to
provide a "good enough" for most uses compatibility layer that gets many tasks done in one codebase.
You may still need to write code against specific versions, especially while this project is new.

**Documentation** of the full API can be found [online at Read the Docs](https://amaptor.readthedocs.io), but here's a trivial example (copying a layer),
but uses some of the core methods:

```python
	import amaptor
	project = amaptor.Project("path_to_pro_project_or_arcmap_document")  # projects abstract away Map Documents and ArcGIS Pro Projects
	my_map = project.maps[0]  # maps abstract away ArcMap data frames and ArcGIS Pro maps
	layer = my_map.find_layer(name="name_of_layer_to_locate")  # new method "find layer" - can find by name or path
	my_map.insert_layer_by_name_or_path(layer, near_name="name_of_other_layer_to_insert_near")
	# new method that inserts a provided layer in the TOC relative to another layer whose name or path is given
	project.save()  # saves, just as in normal API
```

You'll notice that some parts of the API are new. I've added convenience functions for common tasks, but will work on fleshing
out the core API for normal calls as well. I plan to follow the ArcGIS Pro API where possible (but lowercasing and underscoring names)
to keep concepts similar.

## Installation
amaptor is available on PyPI and can be installed via `pip install amaptor` or by cloning this repository and running
`setup.py install`

## Limitations
When using amaptor with existing files, you should plan to have template documents for each version, because ArcGIS Pro projects cannot be
imported back into ArcMap. If you provide an MXD on ArcGIS Pro, amaptor will import it into an ArcGIS Pro project automatically,
but cannot do the same for Pro Projects using ArcMap/arcpy.mapping. See below for an example:

```python
	import amaptor
	
	PRO_TEMPLATE = "path_to_pro_aprx_file"
	ARCMAP_TEMPLATE = "path_to_similar_mxd"
	
	if amaptor.PRO:  # can also reverse and test if amaptor.ARCMAP
		project = amaptor.Project(PRO_TEMPLATE)
	else:
		project = amaptor.Project(ARCMAP_TEMPLATE)
		
	# ... do mapping things with project here

```

This approach will give the best results, though isn't viable in all situations (for example, updating references to data in
ArcGIS Pro Projects on a machine with ArcMap). Still, code that works with templates for the current platform
or creates and manages its own files will work fine with only that slight adjustment.

## Credits and License
By [Nick Santos](https://watershed.ucdavis.edu/people/nick-santos), UC Davis Center for Watershed Sciences and written for projects funded by the State of California.
Licensed under the MIT License.