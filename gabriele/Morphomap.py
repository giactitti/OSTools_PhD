"""
Model exported as python.
Name : MorphoMap
Group : OStools
With QGIS : 32214
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Morphomap(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('2mr', '2mr', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('b03', 'B03', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('b04', 'B04', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('b08', 'B08', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Zs_united', 'ZS_United', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(24, model_feedback)
        results = {}
        outputs = {}

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
            'convergence': 3,
            'depression': None,
            'disturbed_land': None,
            'elevation': parameters['2mr'],
            'flow': None,
            'max_slope_length': None,
            'memory': 300,
            'threshold': 1000,
            'half_basin': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rwatershed'] = processing.run('grass7:r.watershed', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

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

        feedback.setCurrentStep(2)
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

        feedback.setCurrentStep(5)
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

        feedback.setCurrentStep(10)
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

        feedback.setCurrentStep(13)
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

        feedback.setCurrentStep(14)
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

        feedback.setCurrentStep(15)
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

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # EL_A
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['Zs_el']['OUTPUT'],
            'JOIN': outputs['Sz_a']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_a'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # El_S
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_a']['OUTPUT'],
            'JOIN': outputs['Sz_s']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_s'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # El_PC
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_s']['OUTPUT'],
            'JOIN': outputs['Sz_pc']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_pc'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # El_TC
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_pc']['OUTPUT'],
            'JOIN': outputs['Sz_tc']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_tc'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # El_MaxC
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_tc']['OUTPUT'],
            'JOIN': outputs['Sz_maxc']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_maxc'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # El_MinC
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_maxc']['OUTPUT'],
            'JOIN': outputs['Sz_minc']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_minc'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # El_NDVI
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_minc']['OUTPUT'],
            'JOIN': outputs['Sz_ndvi']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['El_ndvi'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # ZS_United
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['El_ndvi']['OUTPUT'],
            'JOIN': outputs['Sz_ndwi']['OUTPUT'],
            'JOIN_FIELDS': [''],
            'METHOD': 0,  # Crea elementi separati per ciascun elemento corrispondente (uno-a-molti)
            'PREDICATE': [2],  # uguale
            'PREFIX': '',
            'OUTPUT': parameters['Zs_united']
        }
        outputs['Zs_united'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Zs_united'] = outputs['Zs_united']['OUTPUT']
        return results

    def name(self):
        return 'MorphoMap'

    def displayName(self):
        return 'MorphoMap'

    def group(self):
        return 'OStools'

    def groupId(self):
        return 'FFM'

    def createInstance(self):
        return Morphomap()
