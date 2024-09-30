from qgis.core import (
    QgsProcessing, 
    QgsProcessingAlgorithm, 
    QgsProcessingMultiStepFeedback, 
    QgsProcessingParameterVectorLayer, 
    QgsProcessingParameterRasterLayer, 
    QgsProcessingParameterFeatureSink, 
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterVectorDestination,
    QgsFields, 
    QgsField, 
    QgsFeature, 
    QgsWkbTypes, 
    QgsGeometry, 
    QgsFeatureSink
)
from qgis.PyQt.QtCore import QVariant
import processing
import rasterio
import rasterio.mask
import numpy as np
from shapely.geometry import shape, Point
import geopandas as gpd

class HighestElevationPointAndLeastCostPathAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        # 入力: ポリゴンレイヤー（地滑り領域）
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'landslide_polygon', 
                'Landslide Polygon', 
                types=[QgsProcessing.TypeVectorPolygon], 
                defaultValue=None
            )
        )
        # 入力: DEM（災害後のデジタル標高モデル）
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                'post_disaster_dem', 
                'Post-disaster DEM', 
                defaultValue=None
            )
        )
        # 出力: 最高標高点のポイントレイヤー
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                'highest_elevation_point', 
                'Highest Elevation Point', 
                type=QgsProcessing.TypeVectorPoint, 
                createByDefault=True, 
                defaultValue=None
            )
        )
        # 出力: 土砂崩れプロファイルライン（Least Cost Path）
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'landslide_profile_line', 
                'Landslide Profile Line (Least Cost Path)', 
                type=QgsProcessing.TypeVectorAnyGeometry, 
                defaultValue=None
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # 進捗管理のためのフィードバック
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # DEM と ポリゴンレイヤーを取得
        dem_layer = self.parameterAsRasterLayer(parameters, 'post_disaster_dem', context)
        polygon_layer = self.parameterAsVectorLayer(parameters, 'landslide_polygon', context)
        # QGIS の FeatureSink を用いてポイントレイヤーを保存
        (sink, dest_id) = self.parameterAsSink(
            parameters, 
            'highest_elevation_point', 
            context, 
            QgsFields([
                QgsField('value', QVariant.Double)
            ]), 
            QgsWkbTypes.Point, 
            polygon_layer.crs()
        )

        alg_params={
            'dem_layer': dem_layer,
            'polygon_layer':polygon_layer
        }
        self.maxminelevation(alg_params)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # 最小コスト経路（Least Cost Path）を計算
        # ここでは Flow Accumulation のデータが必要です。必要な処理を呼び出します。
        alg_params = {
            'DEM': dem_layer.source(),
            'DZFILL': 0,
            'PREPROC': 0,
            'FLOW': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FlowAccumulationQmOfEsp'] = processing.run('sagang:flowaccumulationqmofesp', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['flow_accumulation'] = outputs['FlowAccumulationQmOfEsp']['FLOW']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Least Cost Paths の計算
        alg_params = {
            'DEM': outputs['FlowAccumulationQmOfEsp']['FLOW'],
            'SOURCE': QgsGeometry.fromPointXY(highest_elevation_points[0]),  # 最高標高点を出発点に設定
            'VALUES': None,
            'LINE': parameters['landslide_profile_line'],
            'POINTS': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LeastCostPaths'] = processing.run('sagang:leastcostpaths', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['landslide_profile_line'] = outputs['LeastCostPaths']['LINE']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        return results

    def name(self):
        return 'highest_elevation_point_and_least_cost_path'

    def displayName(self):
        return 'Calculate Highest Elevation Point and Least Cost Path'

    def group(self):
        return 'Elevation Tools'

    def groupId(self):
        return 'elevation_tools'

    def createInstance(self):
        return HighestElevationPointAndLeastCostPathAlgorithm()
    
    def maxminelevation(self, parameters):
        # GeoDataFrame を用意して、結果を格納する
        output_points = gpd.GeoDataFrame(columns=['value'], geometry=[])
        
        with rasterio.open(parameters['dem_layer'].source()) as src:
            for feature in parameters['polygon_layer'].getFeatures():
                geom = feature.geometry()
                geom_json = geom.asJson()
                geom_shape = shape(eval(geom_json))  # ポリゴンのジオメトリ

                # DEMデータをポリゴンでマスクし、対象領域を抽出
                out_image, out_transform = rasterio.mask.mask(src, [geom_shape], crop=True)
                
                # 最高標高点の計算
                max_value_index = np.argmax(out_image[0])
                ind = np.unravel_index(max_value_index, out_image[0].shape)
                max_value = out_image[0][ind]
                lon, lat = rasterio.transform.xy(out_transform, ind[0], ind[1])
                point = Point(lon, lat)
                
                # GeoDataFrameに最高標高点の座標と値を格納
                output_points.loc[len(output_points)] = {'value': max_value, 'geometry': point}
        
        # CRSの設定（ポリゴンレイヤーのCRSを使用）
        output_points.crs = polygon_layer.crs().toWkt()



        highest_elevation_points = []
        for idx, row in output_points.iterrows():
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromWkt(row['geometry'].wkt))
            feat.setAttributes([row['value']])
            sink.addFeature(feat, QgsFeatureSink.FastInsert)
            highest_elevation_points.append(feat.geometry().asPoint())  # 高度の高いポイントを記録
