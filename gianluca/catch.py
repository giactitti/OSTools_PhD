from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterPoint,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorDestination,
    QgsProcessing,
    QgsPointXY,
    QgsCoordinateTransform,
    QgsProject
)
import processing
import shutil

class tc(QgsProcessingAlgorithm):
    
    def name(self):
        # Qui definisco il nome interno dell'algoritmo
        return 'tc'
    
    def displayName(self):
        # Qui metto il nome che apparirà nell'interfaccia QGIS
        return 'Catchment Analysis'
    
    def createInstance(self):
        # Qui creo una nuova istanza della classe per QGIS
        return tc()  
    
    def initAlgorithm(self, config=None):
        
        
        # Parametro per il DEM (raster di elevazione)
        self.addParameter(
            QgsProcessingParameterRasterLayer('dem', 'DEM')
        )
        
        # Parametro per le coordinate del punto di uscita del bacino
        self.addParameter(
            QgsProcessingParameterPoint('coordinates', 'Outlet coordinates')
        )
        
        # Parametro di output per il bacino idrografico (raster)
        self.addParameter(
            QgsProcessingParameterRasterDestination('Catch', 'Catchment')
        )
        
        # Parametro di output opzionale per il bacino in formato vettoriale
        self.addParameter(
            QgsProcessingParameterVectorDestination('CatchVector', 'Catchment vector', 
                type=QgsProcessing.TypeVectorPolygon, optional=True)
        )
        
        # Parametro di output per l'accumulo di flusso
        self.addParameter(
            QgsProcessingParameterRasterDestination('Facc', 'Flow accumulation')
        )
        
        # Parametro di output per la direzione di flusso
        self.addParameter(
            QgsProcessingParameterRasterDestination('Fdir', 'Flow direction')
        )
        
        # Parametro di output per la pendenza
        self.addParameter(
            QgsProcessingParameterRasterDestination('Slope', 'Slope')
        )
        
        # Parametro di output per l'aspect
        self.addParameter(
            QgsProcessingParameterRasterDestination('Aspect', 'Aspect')
        )
        
        # Parametro di output per la rete idrografica (raster)
        self.addParameter(
            QgsProcessingParameterRasterDestination('StreamRaster', 'Stream raster', optional=True)
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        
        
        # Qui prendo il DEM dai parametri di input
        dem = self.parameterAsRasterLayer(parameters, 'dem', context)
        
        # Ottengo il CRS del DEM (questo sarà il nostro CRS di riferimento)
        dem_crs = dem.crs()
        feedback.pushInfo(f'DEM CRS: {dem_crs.authid()}')
        
        # Qui estraggo le coordinate del punto di uscita
        coords = parameters['coordinates']
        if isinstance(coords, str):
            coord_parts = coords.split('[')[0].strip().split(',')
            x_orig = float(coord_parts[0])
            y_orig = float(coord_parts[1])
            point_crs = QgsProject.instance().crs()
        else:
            x_orig = coords.x()
            y_orig = coords.y()
            point_crs = coords.crs() if hasattr(coords, 'crs') and coords.crs().isValid() else QgsProject.instance().crs()
        
        feedback.pushInfo(f'Point coordinates: {x_orig}, {y_orig} ({point_crs.authid()})')
        
        # Trasformazione al CRS del DEM se necessario
        if point_crs.authid() == dem_crs.authid():
            x_final = x_orig
            y_final = y_orig
        else:
            feedback.pushInfo(f'Transforming: {point_crs.authid()} -> {dem_crs.authid()}')
            point_geom = QgsPointXY(x_orig, y_orig)
            transform = QgsCoordinateTransform(point_crs, dem_crs, QgsProject.instance())
            try:
                transformed_point = transform.transform(point_geom)
                x_final = transformed_point.x()
                y_final = transformed_point.y()
                feedback.pushInfo(f'Transformed coordinates: {x_final:.3f}, {y_final:.3f}')
            except Exception as e:
                feedback.reportError(f"CRS transformation error: {str(e)}")
                return {}
        
        feedback.pushInfo(f'Using coordinates: {x_final:.3f}, {y_final:.3f} in {dem_crs.authid()}')
        
        # Qui creo la stringa delle coordinate nel formato richiesto da GRASS
        coord_string = f"{x_final},{y_final}"
        
        # Controlla se i parametri opzionali slope e aspect sono stati specificati
        slope_output = self.parameterAsOutputLayer(parameters, 'Slope', context)
        aspect_output = self.parameterAsOutputLayer(parameters, 'Aspect', context)
        
        # Calcolo della pendenza e aspect se almeno uno è richiesto
        slope_aspect_result = None
        if slope_output or aspect_output:
            feedback.pushInfo('Calculating slope and aspect...')
            slope_aspect_result = processing.run("grass7:r.slope.aspect", {
                'elevation': dem,
                'format': 0,  # 0 = degrees, 1 = percent
                'slope': 'TEMPORARY_OUTPUT',
                'aspect': 'TEMPORARY_OUTPUT'
            }, context=context, feedback=feedback)
        
        # Qui eseguo l'algoritmo GRASS r.watershed per calcolare facc e fdir
        watershed_result = processing.run("grass7:r.watershed", {
            'elevation': dem,
            'threshold': 1562,  # Soglia per definire i canali
            'convergence': 5,   # Parametro di convergenza
            'memory': 300,      # Memoria da utilizzare
            'accumulation': 'TEMPORARY_OUTPUT',  # Output temporaneo per facc
            'drainage': 'TEMPORARY_OUTPUT',      # Output temporaneo per fdir
            'stream': 'TEMPORARY_OUTPUT'         # Output temporaneo per streams
        }, context=context, feedback=feedback)
        
        # inizializzo il dizionario dei risultati
        results = {}
        
        # Gestisco l'output della pendenza se richiesto
        if slope_output and slope_aspect_result:
            shutil.copy2(slope_aspect_result['slope'], slope_output)
            results['Slope'] = slope_output
        
        # Gestisco l'output dell'aspect se richiesto
        if aspect_output and slope_aspect_result:
            shutil.copy2(slope_aspect_result['aspect'], aspect_output)
            results['Aspect'] = aspect_output
        
        #gestisco l'output dell'accumulo di flusso se richiesto
        if parameters['Facc']:
            facc_output = self.parameterAsOutputLayer(parameters, 'Facc', context)
            # Copio il file temporaneo nella destinazione finale
            shutil.copy2(watershed_result['accumulation'], facc_output)
            results['Facc'] = facc_output
        
        #gestisco l'output della direzione di drenaggio se richiesto
        if parameters['Fdir']:
            fdir_output = self.parameterAsOutputLayer(parameters, 'Fdir', context)
            feedback.pushInfo(f'Copying drainage from: {watershed_result["drainage"]}')
            feedback.pushInfo(f'Copying drainage to: {fdir_output}')
            # Copio il file temporaneo nella destinazione finale
            shutil.copy2(watershed_result['drainage'], fdir_output)
            results['Fdir'] = fdir_output
        
        #gestisco l'output del raster stream se richiesto
        if parameters['StreamRaster']:
            stream_output = self.parameterAsOutputLayer(parameters, 'StreamRaster', context)
            shutil.copy2(watershed_result['stream'], stream_output)
            results['StreamRaster'] = stream_output
        
        #gestisco il calcolo del bacino idrografico se richiesto
        if parameters['Catch']:
            feedback.pushInfo(f'Calculating catchment for coordinates: {coord_string}')
            
            # Uso r.water.outlet per calcolare il bacino dal punto specificato
            catchment_result = processing.run("grass7:r.water.outlet", {
                'input': watershed_result['drainage'],  # Uso la direzione di drenaggio calcolata prima
                'output': 'TEMPORARY_OUTPUT',
                'coordinates': coord_string  # Le coordinate del punto di uscita
            }, context=context, feedback=feedback)
            
            # copio il risultato del bacino nella destinazione finale
            catch_output = self.parameterAsOutputLayer(parameters, 'Catch', context)
            shutil.copy2(catchment_result['output'], catch_output)
            results['Catch'] = catch_output
            
            # Controlla se il parametro opzionale CatchVector è stato specificato
            vector_output = self.parameterAsOutputLayer(parameters, 'CatchVector', context)
            
            #  conversione in vettoriale se richiesta
            if vector_output:
                feedback.pushInfo('Converting catchment to vector...')
                
                # Prima converto tutto il raster in poligoni
                temp_vector = processing.run("gdal:polygonize", {
                    'INPUT': catchment_result['output'],
                    'BAND': 1,
                    'FIELD': 'DN',  # Campo che conterrà i valori del raster
                    'EIGHT_CONNECTEDNESS': False,
                    'EXTRA': '',
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }, context=context, feedback=feedback)
                
                # filtro solo i poligoni che rappresentano il bacino (DN = 1)
                filtered_vector = processing.run("native:extractbyexpression", {
                    'INPUT': temp_vector['OUTPUT'],
                    'EXPRESSION': '"DN" = 1',  # Tengo solo i poligoni con valore 1
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }, context=context, feedback=feedback)
                
                # Qui aggiungo i campi per area e tempo di corrivazione al vettore
                temp_with_area = processing.run("native:fieldcalculator", {
                    'INPUT': filtered_vector['OUTPUT'],
                    'FIELD_NAME': 'Area_km2',
                    'FIELD_TYPE': 0,  # Float
                    'FIELD_LENGTH': 20,
                    'FIELD_PRECISION': 6,
                    'FORMULA': '$area / 1000000',  # Converto da m² a km²
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }, context=context, feedback=feedback)
                
                # aggiungo il tempo di corrivazione usando la formula di Pilgrim
                temp_with_tc = processing.run("native:fieldcalculator", {
                    'INPUT': temp_with_area['OUTPUT'],  # Uso l'output del calcolo precedente
                    'FIELD_NAME': 'Tc_ore',
                    'FIELD_TYPE': 0,  # Float
                    'FIELD_LENGTH': 20,
                    'FIELD_PRECISION': 3,
                    'FORMULA': '0.76 * (("Area_km2") ^ 0.38)',  # Formula di Pilgrim: Tc = 0.76 * A^0.38
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }, context=context, feedback=feedback)
                
                # calcolo la quota media del bacino usando le statistiche zonali
                temp_with_elevation = processing.run("native:zonalstatisticsfb", {
                    'INPUT': temp_with_tc['OUTPUT'],
                    'INPUT_RASTER': dem,
                    'RASTER_BAND': 1,
                    'COLUMN_PREFIX': 'elev_',
                    'STATISTICS': [2],  # Solo la media (2 = mean)
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                }, context=context, feedback=feedback)
                
                # Aggiungo le statistiche della pendenza se disponibile
                if slope_aspect_result and slope_output:
                    feedback.pushInfo('Adding slope statistics to catchment vector...')
                    temp_with_slope = processing.run("native:zonalstatisticsfb", {
                        'INPUT': temp_with_elevation['OUTPUT'],
                        'INPUT_RASTER': slope_aspect_result['slope'],
                        'RASTER_BAND': 1,
                        'COLUMN_PREFIX': 'slope_',
                        'STATISTICS': [2, 5, 6],  # Media (2), Min (5), Max (6)
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                    }, context=context, feedback=feedback)
                    temp_with_elevation = temp_with_slope
                
                # Aggiungo le statistiche dell'aspect se disponibile
                if slope_aspect_result and aspect_output:
                    feedback.pushInfo('Adding aspect statistics to catchment vector...')
                    temp_with_aspect = processing.run("native:zonalstatisticsfb", {
                        'INPUT': temp_with_elevation['OUTPUT'],
                        'INPUT_RASTER': slope_aspect_result['aspect'],
                        'RASTER_BAND': 1,
                        'COLUMN_PREFIX': 'aspect_',
                        'STATISTICS': [2, 5, 6],  # Media (2), Min (5), Max (6)
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                    }, context=context, feedback=feedback)
                    temp_with_elevation = temp_with_aspect
                
                # aggiungo manualmente la quota del punto di chiusura usando le coordinate trasformate
                processing.run("native:fieldcalculator", {
                    'INPUT': temp_with_elevation['OUTPUT'],
                    'FIELD_NAME': 'elev_outlet',
                    'FIELD_TYPE': 0,  # Float
                    'FIELD_LENGTH': 10,
                    'FIELD_PRECISION': 2,
                    'FORMULA': f'raster_value(\'{dem.name()}\', 1, make_point({x_final}, {y_final}))',  
                    'OUTPUT': vector_output
                }, context=context, feedback=feedback)
                
                results['CatchVector'] = vector_output
        
        # Qui restituisco tutti i risultati calcolati
        return results