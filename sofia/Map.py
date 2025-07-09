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
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFileDestination
import processing


class Xartis(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('area_of_interest', 'Area of interest', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('catchment_area', 'Catchment area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('cities', 'Cities', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('name_of_cities', 'Name of cities', type=QgsProcessingParameterField.Any, parentLayerParameterName='cities', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('name_of_the_cathcment', 'Name of the cathcment', type=QgsProcessingParameterField.Any, parentLayerParameterName='area_of_interest', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('regional_boundary', 'Regional Boundary', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('RegionalBoundary_clip', 'Regional Boundary_clip', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='TEMPORARY_OUTPUT'))
        self.addParameter(QgsProcessingParameterFeatureSink('CatchmentArea_clip', 'Catchment area_clip', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='TEMPORARY_OUTPUT'))
        self.addParameter(QgsProcessingParameterFeatureSink('CitiesOfInterest', 'Cities of interest', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFileDestination('Map', 'Map', fileFilter='PDF Format (*.pdf *.PDF)', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(13, model_feedback)
        results = {}
        outputs = {}

        # Extract by location
        alg_params = {
            'INPUT': parameters['cities'],
            'INTERSECT': parameters['area_of_interest'],
            'PREDICATE': [0],  # intersect
            'OUTPUT': parameters['CitiesOfInterest']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['CitiesOfInterest'] = outputs['ExtractByLocation']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Export print layout as PDF
        alg_params = {
            'DISABLE_TILED': False,
            'DPI': None,
            'FORCE_RASTER': False,
            'FORCE_VECTOR': False,
            'GEOREFERENCE': True,
            'IMAGE_COMPRESSION': 0,  # Lossy (JPEG)
            'INCLUDE_METADATA': True,
            'LAYERS': None,
            'LAYOUT': 'Map',
            'SEPARATE_LAYERS': False,
            'SIMPLIFY': True,
            'TEXT_FORMAT': 0,  # Always Export Text as Paths (Recommended)
            'OUTPUT': parameters['Map']
        }
        outputs['ExportPrintLayoutAsPdf'] = processing.run('native:printlayouttopdf', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Map'] = outputs['ExportPrintLayoutAsPdf']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Set layer style
        alg_params = {
            'INPUT': parameters['regional_boundary'],
            'STYLE': 'C:\\Users\\sofia\\UNIBO\\QGIS Course\\periferies.qml'
        }
        outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Set layer style
        alg_params = {
            'INPUT': parameters['catchment_area'],
            'STYLE': 'C:\\Users\\sofia\\UNIBO\\QGIS Course\\ydatikadiamerismata.qml'
        }
        outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': parameters['regional_boundary'],
            'OVERLAY': parameters['area_of_interest'],
            'OUTPUT': parameters['RegionalBoundary_clip']
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['RegionalBoundary_clip'] = outputs['Clip']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': parameters['catchment_area'],
            'OVERLAY': parameters['area_of_interest'],
            'OUTPUT': parameters['CatchmentArea_clip']
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['CatchmentArea_clip'] = outputs['Clip']['OUTPUT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Set layer style
        alg_params = {
            'INPUT': outputs['ExtractByLocation']['OUTPUT'],
            'STYLE': 'C:\\Users\\sofia\\UNIBO\\QGIS Course\\labels.qml'
        }
        outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Set layer style
        alg_params = {
            'INPUT': outputs['Clip']['OUTPUT'],
            'STYLE': 'C:\\Users\\sofia\\UNIBO\\QGIS Course\\ydatikadiamerismata.qml'
        }
        outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Set layer style
        alg_params = {
            'INPUT': outputs['Clip']['OUTPUT'],
            'STYLE': 'C:\\Users\\sofia\\UNIBO\\QGIS Course\\regional boundaries.qml'
        }
        outputs['SetLayerStyle'] = processing.run('native:setlayerstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

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
