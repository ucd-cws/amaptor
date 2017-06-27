import os

_TEMPLATES = os.path.join(os.path.split(os.path.abspath(__file__))[0], "templates")
_PRO_BLANK_TEMPLATE = os.path.join(_TEMPLATES, "pro", "blank_pro_project", "blank_pro_project.aprx")
_PRO_BLANK_LAYOUT = os.path.join(_TEMPLATES, "pro", "blank_layout.pagx")

_BLANK_FEATURE_LAYER = os.path.join(_TEMPLATES, "pro", "blank_layer.lyr")
_BLANK_RASTER_LAYER = os.path.join(_TEMPLATES, "pro", "blank_raster_layer.lyr")