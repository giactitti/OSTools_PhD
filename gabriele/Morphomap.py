"""
Model exported as python.
Name : MorphoMap_
Group : FFM
With QGIS : 32214
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Morphomap_(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('2mr', '2mr', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('b03', 'B03', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('b04', 'B04', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('b08', 'B08', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Merged_basin', 'Merged_Basin', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(17, model_feedback)
        results = {}
        outputs = {}

        # NDVI
        alg_params = {
            'CELLSIZE': 0,
            'CRS': 'ProjectCrs',
            'EXPRESSION': '("B08@1"- "B04@1") / ("B08@1" + "B04@1")',
            'EXTENT': None,
            'LAYERS': [parameters['b04'],parameters['b08']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Ndvi'] = processing.run('qgis:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # r.slope.aspect
        alg_params = {
            '-a': True,
            '-e': False,
            '-n': False,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'elevation': parameters['2mr'],
            'format': 0,  # degrees
            'min_slope': 0,
            'precision': 0,  # FCELL
            'zscale': 1,
            'aspect': QgsProcessing.TEMPORARY_OUTPUT,
            'pcurvature': QgsProcessing.TEMPORARY_OUTPUT,
            'slope': QgsProcessing.TEMPORARY_OUTPUT,
            'tcurvature': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rslopeaspect'] = processing.run('grass7:r.slope.aspect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # r.watershed
        alg_params = {
            '-4': False,
            '-a': False,
            '-b': False,
            '-m': False,
            '-s': True,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'blocking': None,
            'convergence': 5,
            'depression': None,
            'disturbed_land': None,
            'elevation': parameters['2mr'],
            'flow': None,
            'max_slope_length': None,
            'memory': 300,
            'threshold': 3000,
            'half_basin': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rwatershed'] = processing.run('grass7:r.watershed', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Slope, Aspect, Curvature
        alg_params = {
            'ELEVATION': parameters['2mr'],
            'METHOD': 6,  # [6] 9 parameter 2nd order polynom (Zevenbergen & Thorne 1987)
            'UNIT_ASPECT': 0,  # [0] radians
            'UNIT_SLOPE': 0,  # [0] radians
            'ASPECT': QgsProcessing.TEMPORARY_OUTPUT,
            'C_CROS': QgsProcessing.TEMPORARY_OUTPUT,
            'C_GENE': QgsProcessing.TEMPORARY_OUTPUT,
            'C_LONG': QgsProcessing.TEMPORARY_OUTPUT,
            'C_MAXI': QgsProcessing.TEMPORARY_OUTPUT,
            'C_MINI': QgsProcessing.TEMPORARY_OUTPUT,
            'C_PLAN': QgsProcessing.TEMPORARY_OUTPUT,
            'C_PROF': QgsProcessing.TEMPORARY_OUTPUT,
            'C_ROTO': QgsProcessing.TEMPORARY_OUTPUT,
            'C_TANG': QgsProcessing.TEMPORARY_OUTPUT,
            'C_TOTA': QgsProcessing.TEMPORARY_OUTPUT,
            'SLOPE': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SlopeAspectCurvature'] = processing.run('saga:slopeaspectcurvature', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # r.to.vect
        alg_params = {
            '-b': False,
            '-s': False,
            '-t': False,
            '-v': False,
            '-z': False,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,  # auto
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'column': 'value',
            'input': outputs['Rwatershed']['half_basin'],
            'type': 2,  # area
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rtovect'] = processing.run('grass7:r.to.vect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # NDWI
        alg_params = {
            'CELLSIZE': 0,
            'CRS': 'ProjectCrs',
            'EXPRESSION': '("B03@1"- "B08@1") / ("B03@1" + "B08@1")',
            'EXTENT': None,
            'LAYERS': [parameters['b03'],parameters['b08']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Ndwi'] = processing.run('qgis:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Rep_vectorized
        alg_params = {
            'INPUT': outputs['Rtovect']['output'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rep_vectorized'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # ZS_El
        alg_params = {
            'COLUMN_PREFIX': 'El_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': parameters['2mr'],
            'RASTER_BAND': 1,
            'STATISTICS': [6,2,4],  # Massimo,Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Zs_el'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # SZ_TC
        alg_params = {
            'COLUMN_PREFIX': 'TC_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['Rslopeaspect']['tcurvature'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_tc'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # SZ_PC
        alg_params = {
            'COLUMN_PREFIX': 'PC_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['Rslopeaspect']['pcurvature'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_pc'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # SZ_MaxC
        alg_params = {
            'COLUMN_PREFIX': 'MaxC_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['SlopeAspectCurvature']['C_MAXI'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_maxc'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # SZ_S
        alg_params = {
            'COLUMN_PREFIX': 'S_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['Rslopeaspect']['slope'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_s'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # SZ_A
        alg_params = {
            'COLUMN_PREFIX': 'A_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['Rslopeaspect']['aspect'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_a'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # SZ_MinC
        alg_params = {
            'COLUMN_PREFIX': 'MinC_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['SlopeAspectCurvature']['C_MINI'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_minc'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # SZ_NDWI
        alg_params = {
            'COLUMN_PREFIX': 'NDWI_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['SlopeAspectCurvature']['C_MINI'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_ndwi'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # SZ_NDVI
        alg_params = {
            'COLUMN_PREFIX': 'NDVI_',
            'INPUT': outputs['Rep_vectorized']['OUTPUT'],
            'INPUT_RASTER': outputs['Ndvi']['OUTPUT'],
            'RASTER_BAND': 1,
            'STATISTICS': [2,4],  # Media,Dev std
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Sz_ndvi'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Unione
        alg_params = {
            'INPUT': outputs['Zs_el']['OUTPUT'],
            'OVERLAY': None,
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': parameters['Merged_basin']
        }
        outputs['Unione'] = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Merged_basin'] = outputs['Unione']['OUTPUT']
        return results

    def name(self):
        return 'MorphoMap_'

    def displayName(self):
        return 'MorphoMap_'

    def group(self):
        return 'FFM'

    def groupId(self):
        return 'FFM'

    def createInstance(self):
        return Morphomap_()
