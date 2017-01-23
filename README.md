# Amaptor - Arcpy mapping compatibility layer
The goal of Amaptor is to be a map adaptor - providing a single interface
for most mapping needs that works against both arcpy.mapping (ArcMap 10.x/Python 2.7)
and arcpy.mp (ArcGIS Pro/Python 3.4+).

arcpy.mapping and arcpy.mp are separated for _good reason_ - the concepts behind
map documents/projects changed between ArcMap and ArcGIS Pro, so amaptop, as currently
conceptualized isn't meant to guarantee complete functionality in both cases, but to
provide a "good enough" for most uses compatibility layer that gets many tasks done in one codebase.
You may still need to write code against specific versions, especially while this project is new.