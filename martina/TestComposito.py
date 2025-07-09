from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterFeatureSink
import processing

class TestComposito(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('mappa_dati', 'Mappa_dati', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('mask', 'Mask', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('unit_funzionale', 'Unità funzionale', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Mappa_inter', 'Mappa_Inter', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # Clip vector by mask layer
        clip_params = {
            'INPUT': parameters['mappa_dati'],
            'MASK': parameters['mask'],
            'OPTIONS': '',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
        outputs['ClipVectorByMaskLayer'] = processing.run('gdal:clipvectorbypolygon', clip_params, context=context, feedback=feedback, is_child_algorithm=True)
        clipped_layer = outputs['ClipVectorByMaskLayer']['OUTPUT']


        # Intersection
        inter_params = {
            'GRID_SIZE': None,
            'INPUT': clipped_layer,
            'INPUT_FIELDS': [''],
            'OVERLAY': parameters['unit_funzionale'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }
        outputs['Intersection'] = processing.run('native:intersection', inter_params, context=context, feedback=feedback, is_child_algorithm=True)
        inter_layer = outputs['Intersection']['OUTPUT']
        
        # Area
        area_params = {
            'FIELD_LENGTH': 20,
            'FIELD_NAME': 'Area_Km2',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '$area /1000000',
            'INPUT': inter_layer,
            'OUTPUT': parameters['Mappa_inter']
        }
        outputs['FieldCalculator'] = processing.run('native:fieldcalculator', area_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Mappa_inter'] = outputs['FieldCalculator']['OUTPUT']
        return results

    def name(self):
        return 'Test Composito'

    def displayName(self):
        return 'Test Composito (Clip + Intersect)'

    def group(self):
        return 'Custom Script'

    def groupId(self):
        return 'CustomScript'

    def createInstance(self):
        return TestComposito()

