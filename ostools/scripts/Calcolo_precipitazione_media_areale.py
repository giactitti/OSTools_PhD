"""
Model exported as python.
Name : GRID_prec_ERG5
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFeatureSink,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsField,
    edit
)
import processing
from qgis.PyQt.QtCore import QVariant


class Grid_prec_erg5(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('catchment', 'Catchment', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('grid_prec', 'GRID prec', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('CutGridCat', 'Cut GRID CAT', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True))
        self.addParameter(QgsProcessingParameterFeatureSink('ReprojectedGridPrec', 'Reprojected GRID prec', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True))
        self.addParameter(QgsProcessingParameterFeatureSink('CutConAreaCelle', 'Cut con AREA celle', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True))
        self.addParameter(QgsProcessingParameterFeatureSink('PrecipMediaBacino', 'Precip media bacino', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True))

    def processAlgorithm(self, parameters, context, model_feedback):
        feedback = QgsProcessingMultiStepFeedback(7, model_feedback)
        results = {}
        outputs = {}

        # Step 0: Reproject GRID_prec
        alg_params = {
            'CONVERT_CURVED_GEOMETRIES': False,
            'INPUT': parameters['grid_prec'],
            'OPERATION': '',
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:32632'),
            'OUTPUT': parameters['ReprojectedGridPrec']
        }
        outputs['ReprojectLayer'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['ReprojectedGridPrec'] = outputs['ReprojectLayer']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Step 1: Calcola area del bacino
        catchment_layer = self.parameterAsVectorLayer(parameters, 'catchment', context)
        area_bacino = 0.0
        if catchment_layer is not None:
            transform = QgsCoordinateTransform(catchment_layer.crs(), QgsCoordinateReferenceSystem('EPSG:32632'), QgsProject.instance())
            for feat in catchment_layer.getFeatures():
                geom = feat.geometry()
                if geom is not None:
                    geom.transform(transform)
                    area_bacino = geom.area()
                    break
        else:
            raise Exception("Layer catchment non valido")

        feedback.pushInfo(f"Area bacino: {area_bacino}")

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Step 2: Clip GRID_prec con il bacino
        alg_params = {
            'INPUT': outputs['ReprojectLayer']['OUTPUT'],
            'OVERLAY': catchment_layer,
            'OUTPUT': parameters['CutGridCat']
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['CutGridCat'] = outputs['Clip']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Step 3: Calcola area delle celle
        area_calc = processing.run("qgis:fieldcalculator", {
            'INPUT': outputs['Clip']['OUTPUT'],
            'FIELD_NAME': 'area_cella',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 20,
            'FIELD_PRECISION': 5,
            'NEW_FIELD': True,
            'FORMULA': 'area($geometry)',
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Step 4: Aggiungi campo costante con area bacino
        bacino_field = processing.run("qgis:fieldcalculator", {
            'INPUT': area_calc['OUTPUT'],
            'FIELD_NAME': 'area_bacino_const',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 20,
            'FIELD_PRECISION': 5,
            'NEW_FIELD': True,
            'FORMULA': str(area_bacino),
            'OUTPUT': 'TEMPORARY_OUTPUT'
        }, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Step 5: Calcola peso
        peso_output = processing.run("qgis:fieldcalculator", {
            'INPUT': bacino_field['OUTPUT'],
            'FIELD_NAME': 'peso',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 20,
            'FIELD_PRECISION': 5,
            'NEW_FIELD': True,
            'FORMULA': '"area_cella" / "area_bacino_const"',
            'OUTPUT': parameters['CutConAreaCelle']
        }, context=context, feedback=feedback, is_child_algorithm=True)
        results['CutConAreaCelle'] = peso_output['OUTPUT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Step 6: Calcolo dei campi pesati
        layer = self.parameterAsVectorLayer(parameters, 'CutConAreaCelle', context)
        if not layer:
            raise Exception("Impossibile caricare il layer 'CutConAreaCelle'")

        provider = layer.dataProvider()

        # Identifica i campi che iniziano con 'DATA'
        data_fields = [field.name() for field in provider.fields() if field.name().startswith('DATA')]

        # Aggiungi nuovi campi per i valori pesati
        new_fields = [QgsField(f"{name}_pesata", QVariant.Double) for name in data_fields]
        provider.addAttributes(new_fields)
        layer.updateFields()

        # Mappa i nuovi indici dei campi creati
        field_indices = {field.name(): layer.fields().indexOf(field.name()) for field in new_fields}

        with edit(layer):
            for feat in layer.getFeatures():
                peso = feat['peso']
                for name in data_fields:
                    val = feat[name]
                    val_pesato = val * peso if val is not None else None
                    feat.setAttribute(field_indices[f"{name}_pesata"], val_pesato)
                layer.updateFeature(feat)

        return results

    def name(self):
        return 'GRID_prec_ERG5'

    def displayName(self):
        return 'GRID_prec_ERG5'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Grid_prec_erg5()

