from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from osgeo import gdal
import numpy as np
import processing


class Model(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('waste_dumps_dem', 'Waste Dumps DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('shapefile_waste_dump', 'Shapefile Waste Dump', defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # Clip raster by mask layer
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': parameters['waste_dumps_dem'],
            'KEEP_RESOLUTION': False,
            'MASK': parameters['shapefile_waste_dump'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': None,
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipRasterByMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        print(outputs['ClipRasterByMaskLayer']['OUTPUT'])
        raster = gdal.Open(outputs['ClipRasterByMaskLayer']['OUTPUT'])
        band = raster.GetRasterBand(1)
        raster_matrix = band.ReadAsArray()
        print(raster_matrix)
        min_value = np.min(raster_matrix[raster_matrix>0])
        max_value = np.max(raster_matrix)
        
        # Get GeoTransform
        gt = raster.GetGeoTransform()
        # Pixel size
        pixel_width = gt[1]      # X pixel size
        print(min_value)
        print(max_value)
        
        # Create constant raster layer
        alg_params = {
            'CREATE_OPTIONS': None,
            'EXTENT': ('-7.110972222,-7.095694444,37.595138889,37.603472222 [EPSG:4326]'),
            'NUMBER': (int(min_value)),
            'OUTPUT_TYPE': 5,  # Float32
            'PIXEL_SIZE': pixel_width,
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CreateConstantRasterLayer'] = processing.run('native:createconstantrasterlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        
        # Raster calculator
        alg_params = {
            'CELL_SIZE': None,
            'CRS': None,
            'EXPRESSION': '"B@1" - "A@1"',
            'EXTENT': ('-7.110972222,-7.095694444,37.595138889,37.603472222 [EPSG:4326]'),
            'LAYERS': [outputs['CreateConstantRasterLayer']['OUTPUT'],'OUTPUT_91f36303_3b0e_4f30_a4b3_3109be6eedef'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RasterCalculator'] = processing.run('native:modelerrastercalc', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['DerivedDem'] = outputs['RasterCalculator']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Raster surface volume
        alg_params = {
            'BAND': 1,
            'INPUT': outputs['RasterCalculator']['OUTPUT'],
            'LEVEL': pixel_width,
            'METHOD': 0,  # Count Only Above Base Level
        }
        outputs['CreateConstantRasterLayer'] = processing.run('native:createconstantrasterlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'model'

    def displayName(self):
        return 'model'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Model()