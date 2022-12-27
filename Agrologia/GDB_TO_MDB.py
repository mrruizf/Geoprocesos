import os
import pandas as pd
#import sys
#import re
#reload(sys)
#sys.setdefaultencoding('utf-8')

data = pd.read_csv(r'C:\Users\marlon.ruiz\Downloads\pandas.txt', delimiter = ',',dtype={'MpCodigo':str})
folder = r"\\172.26.0.20\SubAgrologia\Datos_Abiertos\DATOS_ABIERTOS_2022\AHT"
#folder_salida = r"\\172.26.0.20\SubAgrologia\Datos_Abiertos\DATOS_ABIERTOS_2022\AHT\1_PUBLICACION"
folder_salida = r"D:\gdb"
#lista = []
lista_path = []
for path, directories, files in os.walk(folder):
    for name in files:
        if name.endswith(".mdb"):
            try:
                #print(os.path.join(path,name)+"\t--\n"+name[4:])
                #lista.append(name)
                lista_path.append(os.path.join(path,name))
                #arcpy.ExportXMLWorkspaceDocument_management(os.path.join(folder_salida,name), os.path.join(folder_salida,name[:-4]+".xml"), "SCHEMA_ONLY", "BINARY", "METADATA")
                #arcpy.CreateFileGDB_management(path,name[:-4] + ".gdb")
            except:
                next

lista1 = []
for i in lista_path:
    print(i)
    mdb = i.split("\\")[-1]
    if len(mdb.split("_"))<=2:
        print("entra")
        lista1.append(i)

df1 = pd.DataFrame(lista1).rename(columns={0:'ruta'})
df1 = df1['ruta'].str.split('\\', expand=True)
df1["Ruta"] = r"\\172.26.0.20\SubAgrologia\Datos_Abiertos\DATOS_ABIERTOS_2022\AHT\\"[:-1] + df1[7] + "\\" + df1[8]+"\\"+df1[9]
df1 = df1[df1[9]!= 'mdb']
df1 = df1[['Ruta',9]]
df1 = pd.concat([df1, df1[9].str.split('_', expand=True)], axis=1)
df1 = df1.rename(columns={0:'divipola',1:'anio',9:'mdb'})

#df1 = pd.DataFrame(lista1).rename(columns={0:'divipola',1:'anio'})
#df1['mdb'] = df1['divipola']+"_"+df1['anio']

df = pd.merge(df1,data,left_on='divipola',right_on='MpCodigo')

df['Depto'] = df['Depto'].str.decode('utf-8')
df['Depto'] = df['Depto'].str.replace(u"á", "a")
df['Depto'] = df['Depto'].str.replace(u"é", "e")
df['Depto'] = df['Depto'].str.replace(u"í", "i")
df['Depto'] = df['Depto'].str.replace(u"ó", "o")
df['Depto'] = df['Depto'].str.replace(u"ú", "u")
df['Depto'] = df['Depto'].str.replace(u"ñ", "n")

df['MpNombre'] = df['MpNombre'].str.decode('utf-8')
df['MpNombre'] = df['MpNombre'].str.replace(u"á", "a")
df['MpNombre'] = df['MpNombre'].str.replace(u"Á", "A")
df['MpNombre'] = df['MpNombre'].str.replace(u"é", "e")
df['MpNombre'] = df['MpNombre'].str.replace(u"í", "i")
df['MpNombre'] = df['MpNombre'].str.replace(u"Í", "I")
df['MpNombre'] = df['MpNombre'].str.replace(u"ó", "o")
df['MpNombre'] = df['MpNombre'].str.replace(u"ú", "u")
df['MpNombre'] = df['MpNombre'].str.replace(u"ñ", "n")
df['MpNombre'] = df['MpNombre'].str.replace(u"-", " ")
df['MpNombre'] = df['MpNombre'].str.replace(u"ü", "u")
df['MpNombre'] = df['MpNombre'].str.replace(u"Ú", "U")

#df[df['divipola'] == '05360']
df['folder'] = "AHT_"+df['divipola']+"_"+df['Depto'].str[:3]+"_"+df['MpNombre'].str.replace(u" ", "")+"_"+df['anio'].str.replace(u".mdb", "")

for i in range(len(df)):
    path = folder_salida+"\\"+str(df.iloc[i]['Depto'])
    if os.path.isdir(path)==False:
        os.makedirs(path)
        print(path)
    path2 = path+"\\"+str(df.iloc[i]['folder'])
    if os.path.isdir(path2)==False:
        os.makedirs(path2)
        print(path2)
        
import arcpy
no_gen = []
for i in range(len(df)):
    in_data = df.iloc[i]['Ruta']
    out_file = folder_salida+"\\"+str(df.iloc[i]['Depto'])+"\\"+str(df.iloc[i]['folder'])+"\\"+str(df.iloc[i]['folder'])+".xml"
    out_feature = folder_salida+"\\"+str(df.iloc[i]['Depto'])+"\\"+str(df.iloc[i]['folder'])+"\\"+str(df.iloc[i]['folder'])+".gdb\\AREA_HOMOGENEA_TIERRA"
    try:
        if arcpy.Exists(out_feature)==False and arcpy.Exists(in_data+"\\AHT\\AREA_HOMOGENEA_TIERRA")==True:
            arcpy.management.ExportXMLWorkspaceDocument(in_data, out_file)
            arcpy.env.scratchWorkspace = folder_salida+"\\"+str(df.iloc[i]['Depto'])+"\\"+str(df.iloc[i]['folder'])
            arcpy.management.ImportXMLWorkspaceDocument(arcpy.env.scratchGDB, out_file)
            arcpy.management.CreateFileGDB(folder_salida+"\\"+str(df.iloc[i]['Depto'])+"\\"+str(df.iloc[i]['folder']), str(df.iloc[i]['folder'])+".gdb")
            arcpy.env.workspace = arcpy.env.scratchGDB+"\\AHT"
            if arcpy.Exists(arcpy.env.scratchGDB+"\\AHT\\AREA_HOMOGENEA_TIERRA")==True:
                fd_objects = arcpy.ListDatasets(wild_card=None, feature_type='Topology')
                if len(fd_objects)>0:
                    arcpy.management.Delete(arcpy.env.scratchGDB+"\\AHT\\"+fd_objects[0])
                arcpy.Project_management(in_dataset=arcpy.env.scratchGDB+"\\AHT\\AREA_HOMOGENEA_TIERRA", out_dataset=out_feature, out_coor_system="PROJCS['MAGNA-SIRGAS_Origen-Nacional',GEOGCS['GCS_MAGNA',DATUM['D_MAGNA',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',5000000.0],PARAMETER['False_Northing',2000000.0],PARAMETER['Central_Meridian',-73.0],PARAMETER['Scale_Factor',0.9992],PARAMETER['Latitude_Of_Origin',4.0],UNIT['Meter',1.0]]", transform_method="", in_coor_system="PROJCS['MAGNA_Colombia_Bogota',GEOGCS['GCS_MAGNA',DATUM['D_MAGNA',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',1000000.0],PARAMETER['False_Northing',1000000.0],PARAMETER['Central_Meridian',-74.07750791666666],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',4.596200416666666],UNIT['Meter',1.0]]", preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")
                arcpy.management.Delete(arcpy.env.scratchGDB)
                arcpy.management.Delete(out_file)
                print("Finalizado")
            else:
                print("No es posible abrir el dataset")
        else:
            print("Ya se realizó el proceso"+str(out_file))
    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        print(u"Error de Arcpy:\n {}".format(msgs))
        pass
    except Exception:
        no_gen.append(df.iloc[i]['Ruta'])
        print("No realizado")
        pass
#df2 = pd.merge(df1,data, how='right',left_on='divipola',right_on='MpCodigo')
#df.to_csv(r'C:\Users\marlon.ruiz\Downloads\pandas_1.txt', header=True, index=None, sep=',')
                
"""
#######################################################

for i in range(len(df)):
    print(df.iloc[i]['Ruta'])

def normalizar(s):
    replacements = (
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "o"),
        ("ú", "u"),
        ("Á", "A"),
        ("É", "E"),
        ("Í", "I"),
        ("Ó", "O"),
        ("Ú", "U"),
        ("Ñ", "N"),
    )
    for a, b in replacements:
        s = s.replace(a, b).replace(a.upper(), b.upper())
    return s

for i in range(len(df)):
    print(df.iloc[i]['Depto'])
    print("\n")
    print(normalizar(str(df.iloc[i]['Depto'])))
    df.iloc[i]['Departamento'] = normalizar(str(df.iloc[i]['Depto']))
   
df['Departamento'] = df['Depto'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')


for i in range(len(df)):
    #print(df.iloc[i]['divipola'])
    #path = os.path.join(folder_salida,str(df.iloc[i]['Depto']).decode('unicode_escape').encode("latin-1"))
    path = folder_salida+"\\"+str(df.iloc[i]['Depto'])
    if os.path.isdir(path)==False:
        os.makedirs(path)
        print(path)
        
##########################################################################################

import unidecode
df['Departamento'] = unidecode.unidecode(df['Depto'])
df['Departamento'] = df['Depto'].str.decode('iso-8859-1')
for i in range(len(df)):
    df.iloc[i]['Departamento'] = remove_accents(str(df.iloc[i]['Departamento']))

df['Departamento'] = df['Depto'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

import unicodedata
#falta funcion
def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD')
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

for i in range(len(df)):
    df.iloc[i]['Departamento'] = remove_accents(str(df.iloc[i]['Departamento']))

unicodedata.normalize('NFKD', df['Depto']).encode('ascii','ignore')
df['Departamento'] = df['Depto'].apply(remove_accents)"""
