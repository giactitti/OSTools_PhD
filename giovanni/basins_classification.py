"""
Model exported as python.
Name : basins_classification_with_categorical_shape
Group : 
With QGIS : 34008
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProject
from qgis.core import QgsVectorLayer
from qgis.core import QgsProcessingParameterRasterLayer
import processing
import os


class Basins_classification_with_categorical_shape(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('categorizedareas', 'Categorized areas', defaultValue=None))
        # self.addParameter(QgsProcessingParameterVectorLayer('basinshapes', 'Basin shapes', defaultValue=None))
        self.addParameter(QgsProcessingParameterMultipleLayers('basinshapefiles', 'Basin shapefiles', layerType=QgsProcessing.TypeVector, defaultValue=None))
        self.addParameter(QgsProcessingParameterString('fieldnametorasterize', 'Name of the vector layer field to rasterize', multiLine=False, defaultValue='BIOME_INT'))
        self.addParameter(QgsProcessingParameterNumber('rasterizeresolution', 'Resolution of the raster cell (geo units)', type=QgsProcessingParameterNumber.Double, defaultValue=0.01))
        self.addParameter(QgsProcessingParameterRasterDestination('Rasterized', 'Rasterized vector layer', createByDefault=True, defaultValue=None))
        # self.addParameter(QgsProcessingParameterFeatureSink('Basinscategories', 'Basins with categories statistics', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFile('FOLDER', 'Output folder', behavior=QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterRasterLayer('INPUT_RASTER', 'Input raster (optional)', optional=True, ))
        
        
    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}
        
        input_raster = self.parameterAsRasterLayer(parameters, 'INPUT_RASTER', context)
        
        if input_raster is None:
            # Rasterize (vector to raster)
            alg_params = {
                'BURN': 0,
                'DATA_TYPE': 4,  # Int32
                'EXTENT': None,
                'EXTRA': '',
                'FIELD': parameters['fieldnametorasterize'],
                'HEIGHT': parameters['rasterizeresolution'],
                'INIT': None,
                'INPUT': parameters['categorizedareas'],
                'INVERT': False,
                'NODATA': 0,
                'OPTIONS': None,
                'UNITS': 1,  # Georeferenced units
                'USE_Z': False,
                'WIDTH': parameters['rasterizeresolution'],
                'OUTPUT': parameters['Rasterized']
            }
            outputs['RasterizeVectorToRaster'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['Rasterized'] = outputs['RasterizeVectorToRaster']['OUTPUT']
            raster = outputs['RasterizeVectorToRaster']['OUTPUT']
            
        else:
            raster = parameters['INPUT_RASTER']
        
        layers = parameters['basinshapefiles']
        layers = self.parameterAsLayerList(parameters, 'basinshapefiles', context)
        
        output_folder = self.parameterAsFile(parameters, 'FOLDER', context)
        print('output_folder:')
        print(output_folder)
        
        for filename in os.listdir(output_folder):
            file_path = os.path.join(output_folder, filename)
            if os.path.isfile(file_path):
                raise ValueError('there are files in the output folder, please remove them or create a new folder')
        
        for i, layer in enumerate(layers):
            
            layer_name = layer.name()
            print('layer_name')
            print(layer_name)
            
            output_path = os.path.join(output_folder, f"{layer_name}_categories.gpkg")
            print(output_path)
        
            # Fix geometries
            alg_params = {
                'INPUT': layer,
                'METHOD': 1,  # Structure
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['FixGeometries'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            print('fixed geometries done')
            
            # Zonal statistics
            alg_params = {
                'COLUMN_PREFIX': '_',
                'INPUT': outputs['FixGeometries']['OUTPUT'],
                'INPUT_RASTER': raster,
                'RASTER_BAND': 1,
                'STATISTICS': [0,8,9],  # Count,Minority,Majority
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ZonalStatistics'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            print('zonal statistics done')
            
            if i == len(layers)-1: # last layer
                # Zonal histogram
                alg_params = {
                    'COLUMN_PREFIX': 'HISTO_',
                    'INPUT_RASTER': raster,
                    'INPUT_VECTOR': outputs['ZonalStatistics']['OUTPUT'],
                    'RASTER_BAND': 1,
                    'OUTPUT': output_path
                }
            else:
                # Zonal histogram
                alg_params = {
                    'COLUMN_PREFIX': 'HISTO_',
                    'INPUT_RASTER': raster,
                    'INPUT_VECTOR': outputs['ZonalStatistics']['OUTPUT'],
                    'RASTER_BAND': 1,
                    'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
                }
                
            outputs['ZonalHistogram'] = processing.run('native:zonalhistogram', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            print('zonal histogram done')
            
            results[f'{layer_name}_cat'] = outputs['ZonalHistogram']['OUTPUT']
            
            vlayer = QgsVectorLayer(results[f'{layer_name}_cat'], f'{layer_name}_cat', "ogr")
            
            QgsProject.instance().addMapLayer(vlayer)
            
        return results

    def name(self):
        return 'basins_classification_with_categorical_shape'

    def displayName(self):
        return 'Basins classification (with categorical shape)'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Basins_classification_with_categorical_shape()
    
    def shortHelpString(self):
        return self.HelpString()
        
    def HelpString(self):
        return (
        """
        Returs zonal histogram and zonal statistics for selected polygon vector layers, based on categorical surfaces
        Input required are a vector or raster which defines the categories of surface
        """
        )
 
