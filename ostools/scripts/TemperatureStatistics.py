"""
Model exported as python.
Name : GeneralTemp
Group : 
With QGIS : 34008
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterBand
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Modello2(QgsProcessingAlgorithm):
    
    def shortHelpString(self):
        return self.HelpString()
    
    def HelpString(self):
        return(
        """
        The algorithm performs zonal statistics (mean) for all raster bands, updating the vector layer step-by-step, and produces a final vector layer with aggregated statistics for every polygon.
        """
        )

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('temperatureorarie', 'temperatureorarie', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('comuni', 'comuni', defaultValue=None))
        #self.addParameter(QgsProcessingParameterBand('banda', 'Banda', parentLayerParameterName='temperatureorarie', allowMultiple=False, defaultValue=[0]))
        self.addParameter(QgsProcessingParameterFeatureSink('Tempcomuni', 'Tempcomuni', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}
        raster_layer = self.parameterAsRasterLayer(parameters, 'temperatureorarie', context)

        # Ottieni il provider del raster
        provider = raster_layer.dataProvider()

        # Numero di bande
        band_count = provider.bandCount()

        print(band_count)
        
        param_id='temperatureorarie'
        
        # Ciclo su tutte le bande
        listband = [f'{param_id}@{i}' for i in range(1, band_count + 1)]
        
        print(listband)
        
        # Statistiche zonali
        
        for i in range(len(listband)):
            band=listband[i]
            print(band)
            
            if i == 0:
                inputLayer=parameters['comuni']
            else:
                inputLayer=outputs['StatisticheZonali']['OUTPUT']
                
            alg_params = {
                'COLUMN_PREFIX': f'{band}_',
                'INPUT': inputLayer,
                'INPUT_RASTER': parameters['temperatureorarie'],
                #'RASTER_BAND': band,
                'EXPRESSION': band,
                'STATISTICS': [2],  # Media
                'OUTPUT': 'TEMPORARY_OUTPUT'
            }
            if i == len(listband)-1:
                alg_params['OUTPUT']= parameters['Tempcomuni']
                
            outputs['StatisticheZonali'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
           
        results['Tempcomuni'] = outputs['StatisticheZonali']['OUTPUT']
        
        return results

    def name(self):
        return 'General statistics on temperature'

    def displayName(self):
        return 'General statistics on temperature'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Modello2()
