print("ciao")
import geopandas as gpd
import pandas as pd
# Carico il csv con il dataset
df = pd.read_csv("C:/Users/giuditta.smerilli2/Desktop/PhD_courses/GIS_TOOLS/R/Dataset_ERG5/prec.try.csv", sep=";")
print(df)
import re
# estraggo il codice delle celle 
colnames = df.columns[1:]
cell_ids = [int(re.search(r'PREC_(\d{5})', col).group(1)) for col in colnames if re.search(r'PREC_(\d{5})', col)]
print(cell_ids)
# carico lo shp del grigliato
gdf = gpd.read_file("C:/Users/giuditta.smerilli2/Desktop/PhD_courses/GIS_TOOLS/GIS/Grigliato_ERG5.shp")
df_prec = df.copy()
df_prec = df_prec.drop(columns=df_prec.columns[0])  # Rimuove colonna datetime
df_prec.columns = cell_ids  # Rinominazione colonne con codici numerici
# traspone il df
df_long = df_prec.T.reset_index()
df_long.columns = ['Codice'] + [f'prec_{i}' for i in range(len(df_long.columns)-1)]
# join con lo shapefile sulla colonna Codice
gdf_joined = gdf.merge(df_long, on='Codice', how='left')
print(gdf_joined)


