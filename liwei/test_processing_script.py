"""
Model exported as python.
Name : model
Group : 
With QGIS : 32204
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterFeatureSink
import processing

from sklearn.neural_network import MLPClassifier

import geopandas as gpd


class Model(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterVectorLayer('v', 'study_area_for_learning', defaultValue=None))
        self.addParameter(QgsProcessingParameterField('x_learn', 'explanatory_variables', type=QgsProcessingParameterField.Any, parentLayerParameterName='v', allowMultiple=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('y_learn', 'susceptible_unit_flag', type=QgsProcessingParameterField.Any, parentLayerParameterName='v', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('w', 'study_area_for_susceptibility_assessing', defaultValue=None))
        #self.addParameter(QgsProcessingParameterField('x_pred', 'explanatory_variables_assess', type=QgsProcessingParameterField.Any, parentLayerParameterName='w', allowMultiple=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Output', 'study_area_with_predicted_susceptible_units', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(0, model_feedback)
        results = {}
        outputs = {}

        outputs['prediction'] = self.NN(parameters)
        
        results['w'] = parameters['w']
        results['Output'] = outputs['prediction']

        return results

    def name(self):
        return 'model'

    def displayName(self):
        return 'model'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Model()

    def import_dataframe(self, parameters):
        
        return

    def NN(self, parameters):        
        MLP = MLPClassifier(hidden_layer_sizes=(16, 32, 64, 32, 16, 8), random_state=42)  
        
        y_train = parameters['y_learn']
        X_train = parameters['x_learn']
        MLP.fit(X_train, y_train)
                     
        y_pred = MLP.predict(parameters['x_pred'])
        
        return(y_pred)  