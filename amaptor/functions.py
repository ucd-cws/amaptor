import os
import tempfile

import arcpy

from amaptor import log, mp, PRO, mapping, LayerNotFoundError
from amaptor.constants import _PRO_BLANK_TEMPLATE


def _import_mxd_to_new_pro_project(mxd, blank_pro_template=_PRO_BLANK_TEMPLATE, default_gdb="TEMP"):
	"""
		Handles importing an ArcMap Document into an ArcGIS Pro Project. Default Geodatabase is "TEMP" by default, indicating
		a temporary gdb should be created. It can also be "KEEP" to leave it alone, or it can be a path
	:param mxd:
	:param blank_pro_template:
	:param default_gdb:
	:return:
	"""

	log.warning("WARNING: Importing MXD to new Pro Project - if you call .save() it will not save back to original MXD. Use .save_a_copy('new_path') instead.")

	# can safely assume that if this is called, we're running on Pro and that's already been checked

	# copy blank project to new location - template is 1.3+
	blank_project = mp.ArcGISProject(blank_pro_template)
	new_temp_project = tempfile.mktemp(".aprx", "pro_project_import")
	blank_project.saveACopy(new_temp_project)
	del(blank_project)

	# strictly speaking, we don't need to destroy and recreate - should be able to edit original without saving - doing this just to keep things clear
	project = mp.ArcGISProject(new_temp_project)
	project.importDocument(mxd, include_layout=True)

	if default_gdb != "KEEP":  # if we're supposed to modify it
		if default_gdb == "TEMP":
			new_default_gdb = tempfile.mktemp(prefix="amaptor_default_geodatabase", suffix=".gdb")
			arcpy.CreateFileGDB_management(os.path.split(new_default_gdb)[0], os.path.split(new_default_gdb)[1])
			project.defaultGeodatabase = new_default_gdb
		else:  # if it's not KEEP or TEMP it must be a path
			project.defaultGeodatabase = default_gdb

	project.save()

	# return the project path, setup will continue from here
	return new_temp_project


def make_layer_with_file_symbology(feature_class, layer_file, layer_name=None):
	"""
		Given a feature class and a template layer file with symbology, returns a new Layer object that has the layer
		from the layer file with the feature class as its data source. Optionally, layer can be renamed with layer_name
	:param feature_class:
	:param layer_file:
	:param layer_name:
	:return:
	"""
	layer = None
	if PRO:
		layer_file = mp.LayerFile(layer_file)
		for layer in layer_file.listLayers():
			break
	else:
		layer = mapping.Layer(layer_file)

	if layer is None:
		raise LayerNotFoundError("No layer available for copying from layer file")

	if PRO:
		layer.dataSource = feature_class
	else:
		with arcpy.Describe(feature_class) as desc:
			if desc.extension and desc.extension != "":
				name = "{}.{}".format(desc.baseName, desc.extension)
			else:
				name = desc.baseName
			layer.replaceDataSource(desc.path, get_workspace_type(feature_class), name)
	if layer_name:
		layer.name = layer_name

	return layer


def reproject_extent(extent, current_extent):
	"""
		Changes an extent from its current spatial reference to the spatial reference on another extent object
	:param extent:
	:param current_extent:
	:return:
	"""
	return extent.projectAs(current_extent.spatialReference)


def get_workspace_type(dataset_path):
	"""
		Gives us a workspace type that's usable for layer.replaceDataSource in ArcMap based on a dataset path
	:param dataset_path:
	:return:
	"""

	prog_id_mapping = {
		"esriDataSourcesGDB.AccessWorkspaceFactory.1": "ACCESS_WORKSPACE",
		"esriDataSourcesGDB.FileGDBWorkspaceFactory.1": "FILEGDB_WORKSPACE",
		"esriDataSourcesGDB.InMemoryWorkspaceFactory.1": "NONE",
		"esriDataSourcesGDB.SdeWorkspaceFactory.1": "SDE_WORKSPACE",
	}

	dataset_desc = arcpy.Describe(dataset_path)
	workspace = dataset_desc.path

	with arcpy.Describe(workspace) as workspace_desc:
		if workspace_desc.workspaceFactoryProgID in prog_id_mapping:  # if we have the specific name for it here, return that first
			return prog_id_mapping[workspace_desc.workspaceFactoryProgID]
		elif workspace_desc.workspaceType == "FileSystem":
			if dataset_desc.extension == "shp":
				return "SHAPEFILE_WORKSPACE"
			elif dataset_desc.extension in ("xls", "xlsx"):
				return "EXCEL_WORKSPACE"
			elif dataset_desc.extension in ("tab", "csv", "txt"):  # probably not the best way to handle this
				return "TEXT_WORKSPACE"
			elif dataset_desc.dataType == "Raster":
				return "RASTER_WORKSPACE"
		elif dataset_desc.dataType == "Tin":
			return "TIN_WORKSPACE"
		elif workspace_desc.workspaceFactoryProgID == "":
			return "SHAPEFILE_WORKSPACE"  # if we get to here without returning, it's likely a shapefile - there are a few items missing from this conditional - CAD, VPF, etc