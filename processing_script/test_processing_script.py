"""
Model exported as python.
Name : Test_cut
Group : OStools
With QGIS : 32811
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Test_cut(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('r', 'r', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('v', 'v', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Output', 'output', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Clip raster by mask layer
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': parameters['r'],
            'KEEP_RESOLUTION': False,
            'MASK': parameters['v'],
            'MULTITHREADING': False,
            'NODATA': -9999,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'X_RESOLUTION': 20,
            'Y_RESOLUTION': 20,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipRasterByMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Zonal histogram
        alg_params = {
            'COLUMN_PREFIX': 'HISTO_',
            'INPUT_RASTER': outputs['ClipRasterByMaskLayer']['OUTPUT'],
            'INPUT_VECTOR': parameters['v'],
            'RASTER_BAND': 1,
            'OUTPUT': parameters['Output']
        }
        outputs['ZonalHistogram'] = processing.run('native:zonalhistogram', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        alg_params = {
            'hello': 'hello everyone',
        }
        self.custom_function(alg_params)

        results['Output'] = outputs['ZonalHistogram']['OUTPUT']
        
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        return results

    def name(self):
        return 'Test_cut'

    def displayName(self):
        return 'Test_cut'

    def group(self):
        return 'OStools'

    def groupId(self):
        return 'OStools'

    def createInstance(self):
        return Test_cut()

    def custom_function(self,parameters):
        print(parameters['hello'])