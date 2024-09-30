"""
Model exported as python.
Name : Test_cut
Group : OStools
With QGIS : 32204
"""

from qgis.core import QgsProcessing, QgsProcessingAlgorithm, QgsProcessingMultiStepFeedback, QgsProcessingParameterVectorLayer, QgsProcessingParameterFeatureSink, QgsProcessingParameterField
import processing


class Test_cut(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('v', 'study area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('y', 'y', type=QgsProcessingParameterField.Any, parentLayerParameterName='v', allowMultiple=False, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('x', 'x', type=QgsProcessingParameterField.Any, parentLayerParameterName='v', allowMultiple=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('w', 'prediction area', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Output', 'output', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # Merge vector layers
        alg_params = {
            'CRS': None,
            'LAYERS': parameters['v'],
            'OUTPUT': parameters['Output']
        }
        outputs['prediction'] = self.NN(alg_params)
        results['Output'] = outputs['prediction']
        return results

    def name(self):
        return 'Test_cut'

    def displayName(self):
        return 'Test_cut'

    def group(self):
        return 'OStools'

    def groupId(self):
        return 'OStools'

    def createInstance(self):
        return Test_cut()

    def NN(self, parameters):
        sc = StandardScaler()
        nomi=parameters['nomi']
        train=parameters['train']
        test=parameters['testy']
        X_train = sc.fit_transform(train[nomi])
        logistic_regression = LogisticRegression()
        logistic_regression.fit(X_train,train['y'])
        prob_fit=logistic_regression.predict_proba(X_train)[::,1]
        train['SI']=prob_fit
        return(train,test)    