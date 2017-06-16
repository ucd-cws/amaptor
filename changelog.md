# Change Log

## 0.1.2
Added Layer class and refactored *most* other items that return layer object or use layer objects to handle receiving them and to return them
Small changes to how certain errors print messages (they don't automatically anymore - only if you print the error)
Added access to default geodatabase for the project - in ArcMap, it returns arcpy.env.workspace, or a new FGDB, as necessary, so that the workspace is always defined.
Started laying groundwork for layouts to work in ArcMap - a single one by default, but where new we could potentially add new layouts to a "project" by creating a new map document. It won't duplicate all features of Pro, but some may be possible.
Minor bugfixes