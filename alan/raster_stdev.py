"""
Model exported as python.
Name : raster_to_points
Group : 
With QGIS : 34008
"""

import numpy as np
import os
from osgeo import gdal
from qgis.PyQt.QtCore import QFileInfo
from scipy.ndimage import generic_filter
from qgis.core import QgsProject
from qgis.core import QgsRasterLayer
from qgis.core import QgsRasterDataProvider
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterFeatureSink
import processing

class Raster_to_points(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers('raster2', 'raster2', layerType=QgsProcessing.TypeRaster, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Output', 'output', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        rasters = parameters['raster2']
        
        #3D array
        arrays = []
        Window_size=1
        
        for idx,r in enumerate(rasters):
            layer = QgsRasterLayer(r, QFileInfo(r).baseName())
            provider = layer.dataProvider()
            # Raster properties
            extent = layer.extent()
            width = layer.width()
            height = layer.height()
            crs = layer.crs()
            print(crs)

            # Read data into array
            block = provider.block(1, extent, width, height)
            arr = np.array([[block.value(i, j) for i in range(width)] for j in range(height)])
            arrays.append(arr)

            if idx == 0:
                gdal_ds = gdal.Open(r)
                transform = layer.GetGeoTransform()
                projection = gdal_ds.GetProjection()
                gdal_ds = None
        
        
        # Std dev across rasters (per pixel)
        stack = np.stack(arrays, axis=0)  # shape: (n_rasters, rows, cols)
        pixel_std = np.std(stack, axis=0)  # shape: (rows, cols)

        # Apply local spatial std smoothing if Window_size > 1
        if Window_size > 1:
            def local_std(window):
                return np.std(window)

            pixel_std = generic_filter(
                pixel_std,
                local_std,
                size=Window_size,
                mode='nearest'
            )

        # Output as GeoTIFF
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(Output, width, height, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform(transform)
        out_ds.SetProjection(projection)
        out_ds.GetRasterBand(1).WriteArray(pixel_std)
        out_ds.FlushCache()
        out_ds = None
        
        return out_ds

    def name(self):
        return 'std'

    def displayName(self):
        return 'std'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Raster_to_points()

    def shortHelpString(self):
        return self.HelpString()
    def HelpString(self):
        return(
        """
        Spatial variability of precipitation maxima (15 min) by means of standard deviation pixel-per-pixel for different events
        """
        )
