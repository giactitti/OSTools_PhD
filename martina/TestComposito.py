from qgis.core import QgsProcessing
from qgis.core import QgsVectorLayer
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterFeatureSink
import processing

class TestComposito(QgsProcessingAlgorithm):

    def shortHelpString(self):
        return self.HelpString()

    def HelpString(self):
        return (
            "This plugin clips input layers to a mask, intersects them with administrative units, "
            "calculates the area, and aggregates the results by unit."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMultipleLayers('mappe', 'Mappe', layerType=QgsProcessing.TypeVector, defaultValue='LHP'))
        self.addParameter(QgsProcessingParameterVectorLayer('mask', 'Mask', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue='REG'))
        self.addParameter(QgsProcessingParameterVectorLayer('unit_funzionale', 'Unità funzionale', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue='COM'))
        self.addParameter(QgsProcessingParameterField('ISTAT', 'ISTAT', type=QgsProcessingParameterField.Any, parentLayerParameterName='unit_funzionale', allowMultiple=False, defaultValue='ISTAT'))
        self.addParameter(QgsProcessingParameterField('COMUNE', 'COMUNE', type=QgsProcessingParameterField.Any, parentLayerParameterName='unit_funzionale', allowMultiple=False, defaultValue='NOME_C'))
        self.addParameter(QgsProcessingParameterField('PROVINCIA', 'PROVINCIA', type=QgsProcessingParameterField.Any, parentLayerParameterName='unit_funzionale', allowMultiple=False, defaultValue='SG_PRV'))
        self.addParameter(QgsProcessingParameterFeatureSink('mappa_join', 'Result', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}
        print(parameters)

        # Ciclo for
        
        for count,mappe in enumerate(parameters['mappe']):

            vector=QgsVectorLayer(mappe,'','ogr')

            # Estrai "alta", "media" o "bassa" dal campo scenario
            scenario_value = ''
            for feat in vector.getFeatures():
                scenario_value = str(feat['per']) 
                break  # solo il primo valore            
                print(scenario_value)

            # Clip vector by mask layer
            clip_params = {
                'INPUT': mappe,
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
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
            outputs['FieldCalculator'] = processing.run('native:fieldcalculator', area_params, context=context, feedback=feedback, is_child_algorithm=True)
            area_layer = outputs['FieldCalculator']['OUTPUT']

            # Agregate
            aggr_params = {
                'AGGREGATES': [{'aggregate': 'count','delimiter': ',','input': '"Area_Km2"','length': 20,'name': 'count','precision': 0,'sub_type': 0,'type': 6,'type_name': 'double precision'},
                {'aggregate': 'first_value','delimiter': ',','input': parameters['ISTAT'],'length': 254,'name': 'ISTAT','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                {'aggregate': 'first_value','delimiter': ',','input': parameters['COMUNE'],'length': 50,'name': 'Comune','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                {'aggregate': 'first_value','delimiter': ',','input': parameters['PROVINCIA'],'length': 254,'name': 'Provincia','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},
                {'aggregate': 'sum','delimiter': ',','input': '"Area_Km2"','length': 20,'name': 'scenario_value' ,'precision': 3,'sub_type': 0,'type': 6,'type_name': 'double precision'}],
                'GROUP_BY': parameters['ISTAT'],
                'INPUT': area_layer,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
            outputs['Aggregate'] = processing.run('native:aggregate', aggr_params, context=context, feedback=feedback, is_child_algorithm=True)
            if count==0:
                # Join colonna Area su ISTAT
                joined_params = {
                     'INPUT': parameters['unit_funzionale'],
                     'FIELD': 'ISTAT',
                     'INPUT_2': outputs['Aggregate']['OUTPUT'],
                     'FIELD_2': 'ISTAT',
                     'FIELDS_TO_COPY': scenario_value,
                     'METHOD': 1,
                     'DISCARD_NONMATCHING': False,
                     'OUTPUT': 'TEMPORARY_OUTPUT'
                }
                outputs['JoinAttributes'] = processing.run('native:joinattributestable', joined_params, context=context, feedback=feedback, is_child_algorithm=True)
                joined_layer = outputs['JoinAttributes']['OUTPUT']
            else:
                joined_params = {
                     'INPUT': joined_layer,
                     'FIELD': 'ISTAT',
                     'INPUT_2': outputs['Aggregate']['OUTPUT'],
                     'FIELD_2': 'ISTAT',
                     'FIELDS_TO_COPY': [scenario_value],
                     'METHOD': 1,
                     'DISCARD_NONMATCHING': False,
                     'OUTPUT': 'TEMPORARY_OUTPUT'
                }
                if count==len(parameters['mappe'])-1:
                    joined_params['OUTPUT']=parameters['mappa_join']
                outputs['JoinAttributes'] = processing.run('native:joinattributestable', joined_params, context=context, feedback=feedback, is_child_algorithm=True)
                joined_layer = outputs['JoinAttributes']['OUTPUT']
        results['mappa_join'] = joined_layer
        return results

    def name(self):
        return 'Test Composito'

    def displayName(self):
        return 'Test Composito (Clip+Inter+Area+Aggr)'

    def group(self):
        return 'Custom Script'

    def groupId(self):
        return 'CustomScript'

    def createInstance(self):
        return TestComposito()
