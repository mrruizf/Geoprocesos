import arcpy
aprx = arcpy.mp.ArcGISProject("CURRENT")
map = aprx.listMaps("Map")[0]  # assumes data to be added to first map listed
print(map.name)

import pandas as pd
data = pd.read_csv(r'C:\Users\marlon.ruiz\Downloads\pandas_1.txt', delimiter = ',',dtype={'MpCodigo':str,'divipola':str})
data['gdb']=r"D:\gdb\\"+data['Depto']+"\\"+data['folder']+"\\"+data['folder']+".gdb"
data['xml'] = r"D:\gdb\\"+data['Depto']+"\\"+data['folder']+"\\"+"AHT_"+data['divipola']+"_Metadato_"+data['Depto'].str[:3]+"_"+data['MpNombre'].str.replace(u" ", "")+"_"+data['anio'].str.replace(u".mdb", ".xml")
data['anios'] = data['anio'].str.replace(u".mdb", "")
#data = pd.merge(df1,data,left_on='MpCodigo',right_on='divipola')

for i in range(len(data)):
    shp_path = str(data.iloc[i]['gdb'])+"\AREA_HOMOGENEA_TIERRA"
    try:
        lyr = arcpy.management.MakeFeatureLayer(shp_path, str(data.iloc[i]['folder'])).getOutput(0)
        #map.addLayer(shp_path)
        arcpy.mapping.AddLayer(lyr)
        print(shp_path)
    except Exception as e:
        print("Error: " + str(e.args[0]))
        pass