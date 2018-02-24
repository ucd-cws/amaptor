# Change Log

## 0.1.2.4
[Change] When trying to retrieve an unsupported symbology from a layer when using ArcMap, it now raises NotSupportedError
[Enhancement] Can now pass the path to a layer file to a layer.symbology and have it copy the symbology over

## 0.1.2.3
[Enhancement] Added buffer_factor on Map.zoom_to_layer and Map.set_extent to control space around layers and extents.
[Enhancement] layers now automatically register the map they're attached to when inserting layers or finding on the map
[Fix] Fixed regression in Map.find_layer where providing a layer name would give "AttributeError: 'Layer' object has no attribute 'dataSource'"
[Fix] Maps were being incompletely assigned to map frames in certain instances, causing inability to use zoom_to_layer, and anything that cross-references maps and frames. Fixed.

## 0.1.2.2
[Fix] Major overhaul of how layers set data source in Pro (so that it actually works, at least for Feature Classes, Shapefiles, Rasters)
[Structure] Functions to support that overhaul (getting workspace_factory values for each input data source)
[Change] New maps no longer bring in an associated layout to avoid cluttering project
[New] Added Layout.find_map_frame function and associated MapFrameNotFound error
[New] Added Layout.find_element and Layout.toggle_element functions for managing page element visibility
[tests] Basic tests for data source changes

## 0.1.2.1
Added ability to get and set layer symbology

## 0.1.2
Added Layer class and refactored *most* other items that return layer object or use layer objects to handle receiving them and to return them
Small changes to how certain errors print messages (they don't automatically anymore - only if you print the error)
Added access to default geodatabase for the project - in ArcMap, it returns arcpy.env.workspace, or a new FGDB, as necessary, so that the workspace is always defined.
Started laying groundwork for layouts to work in ArcMap - a single one by default, but where new we could potentially add new layouts to a "project" by creating a new map document. It won't duplicate all features of Pro, but some may be possible.
Minor bugfixes