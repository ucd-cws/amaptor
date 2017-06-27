import unittest

import amaptor
import arcpy

class TestLayer(unittest.TestCase):
	def _test_set_data_source_pro(self, new_source):
		"""
			Needs to be refactored to not use hardcoded local paths
		:return:
		"""
		if not amaptor.PRO:
			print("Not running in PRO, skipping")
			return

		l2 = amaptor.Layer(new_source)  # automatically does the magic required to set data sources
		l = l2.layer_object
		self.assertEqual(l2.data_source, new_source)
		self.assertEqual(l.dataSource, new_source)

	def test_set_data_source_shapefile_pro(self):
		"""
			Needs to be refactored to not use hardcoded local paths
		:return:
		"""
		self._test_set_data_source_pro(new_source = r"C:\Users\dsx\Code\nitrates-2015-mapping\templates\_template\commondata\study-bounds\studybounds.shp")

	def test_data_source_raster_pro(self):
		self._test_set_data_source_pro(new_source = r"C:\Users\dsx\Code\nitrates-2015-mapping\templates\nitrates_template\nitrates_template.gdb\NatmLosses13")


