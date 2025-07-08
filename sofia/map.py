"""
Model exported as python.
Name : xartis
Group : 
With QGIS : 34003
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Xartis(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('oria_diamerismatwn', 'Oria Diamerismatwn', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('perioxi_endiaferontos', 'Perioxi endiaferontos', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('ydatika', 'Ydatika ', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('OriaDiamerismatwn_clip', 'Oria Diamerismatwn_clip', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Ydatika_clip', 'Ydatika_clip', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Clip
        alg_params = {
            'INPUT': parameters['oria_diamerismatwn'],
            'OVERLAY': parameters['perioxi_endiaferontos'],
            'OUTPUT': parameters['OriaDiamerismatwn_clip']
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OriaDiamerismatwn_clip'] = outputs['Clip']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': parameters['ydatika'],
            'OVERLAY': parameters['perioxi_endiaferontos'],
            'OUTPUT': parameters['Ydatika_clip']
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Ydatika_clip'] = outputs['Clip']['OUTPUT']
        return results

    def name(self):
        return 'xartis'

    def displayName(self):
        return 'xartis'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Xartis()
