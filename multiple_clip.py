"""
Model exported as python.
Name : multiple_clip
Group : 
With QGIS : 34008
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterFeatureSink
import processing



    def initAlgorithm(self, config=None):class Multiple_clip(QgsProcessingAlgorithm):

        self.addParameter(QgsProcessingParameterMultipleLayers('raster1', 'raster1', layerType=QgsProcessing.TypeRaster, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('homo_region', 'homo_region', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Output', 'output', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        my_list = []
        rasters = parameters['raster1'] 
        
        for r in rasters:
        
          # Ritaglia raster con maschera
          alg_params = {
              'ALPHA_BAND': False,
              'CROP_TO_CUTLINE': True,
              'DATA_TYPE': 0,  # Usa Il Tipo Dati del Layer in Ingresso
              'EXTRA': '',
              'INPUT': r,
              'KEEP_RESOLUTION': False,
              'MASK': parameters['homo_region'],
              'MULTITHREADING': False,
              'NODATA': None,
              'OPTIONS': None,
              'SET_RESOLUTION': False,
              'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
              'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32632'),
              'TARGET_EXTENT': None,
              'X_RESOLUTION': None,
              'Y_RESOLUTION': None,
              'OUTPUT': parameters['Output']
            }
          outputs['RitagliaRasterConMaschera'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
          results['Output'] = outputs['RitagliaRasterConMaschera']['OUTPUT']
        
        my_list.append(results['Output'])
        
        return my_list

    def name(self):
        return 'multiple_clip'

    def displayName(self):
        return 'multiple_clip'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Multiple_clip()
