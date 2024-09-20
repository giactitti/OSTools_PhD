from qgis.PyQt.QtCore import *
from qgis.utils import iface
import os
import os.path as op
from qgis.core import QgsRasterLayer

class utils:
    @staticmethod
    def import_raster(path):

        if not os.path.exists(path):
            raise Exception("Cannot find file '" + path + "'.")

        try:            
            rlayer=QgsRasterLayer(path, os.path.splitext(op.basename(path))[0],'gdal')
            return rlayer

        except Exception as e:
            raise Exception(str(e))
    
    @staticmethod
    def save_raster(rlayer,outpath):
        try:
            print('path:',outpath)
            outlayer=rlayer
            return outlayer

        except Exception as e:
            raise Exception(str(e))

    