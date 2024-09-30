"""
Model exported as python.
Name : モデル
Group : 
With QGIS : 33410
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterVectorDestination
import processing


class (QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('landslide_polygon', 'landslide_polygon', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('post_disaster_dem', 'post_disaster_dem', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('the_higest_elevation_point', 'the higest elevation point', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Internal_center_point', 'internal_center_point', type=QgsProcessing.TypeVectorPoint, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Fa', 'fa', createByDefault=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterVectorDestination('Landslide_plofile_line', 'landslide_plofile_line', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=''))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # Flow accumulation (qm of esp)
        alg_params = {
            'DEM': parameters['post_disaster_dem'],
            'DZFILL': 0,
            'PREPROC': 0,  # [0] none
            'FLOW': parameters['Fa']
        }
        outputs['FlowAccumulationQmOfEsp'] = processing.run('sagang:flowaccumulationqmofesp', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Fa'] = outputs['FlowAccumulationQmOfEsp']['FLOW']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # 内部保証点（point on surface）
        alg_params = {
            'ALL_PARTS': True,
            'INPUT': parameters['landslide_polygon'],
            'OUTPUT': parameters['Internal_center_point']
        }
        outputs['PointOnSurface'] = processing.run('native:pointonsurface', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Internal_center_point'] = outputs['PointOnSurface']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Least cost paths
        alg_params = {
            'DEM': outputs['FlowAccumulationQmOfEsp']['FLOW'],
            'SOURCE': parameters['the_higest_elevation_point'],
            'VALUES': None,
            'LINE': parameters['Landslide_plofile_line'],
            'POINTS': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LeastCostPaths'] = processing.run('sagang:leastcostpaths', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Landslide_plofile_line'] = outputs['LeastCostPaths']['LINE']
        return results

    def name(self):
        return 'モデル'

    def displayName(self):
        return 'モデル'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return ()
