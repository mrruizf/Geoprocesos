import arcpy
import pandas as pd
sde = r'F:\ArcGIS Pro\RasterCartografia.sde'
arcpy.env.workspace = sde
datasets = arcpy.ListDatasets("RASTER.md*", "Mosaic")

listas = pd.read_csv(r'C:\Users\marlon.ruiz\Documents\Lista.csv', sep='\t')

df1 = pd.DataFrame(columns = ['Mosaic','Paths'])
for i in datasets:
    output = str(i).replace('RASTER.','')
    if output not in list(listas['Mosaic']):
        try:
            arcpy.management.ExportMosaicDatasetPaths(i, arcpy.env.scratchGDB+str('\\')+output)
            arr = arcpy.da.TableToNumPyArray(arcpy.env.scratchGDB+str('\\')+output, 'Path')
            mosaic = len(arr)*[output]
            dic = {'Mosaic':mosaic,'Paths':arr}
            df2 = pd.DataFrame(dic)
            df1 = df1.append(df2)
            print(i)
        except arcpy.ExecuteError:
            msgs = arcpy.GetMessages(2)
            print(u"Error de Arcpy (Verificar el licenciamiento del conjunto de herramientas Spatial Analyst):\n {}".format(msgs))
            pass

df1.to_csv(r'C:\Users\marlon.ruiz\Documents\Lista1.csv', index = False,sep ='\t')