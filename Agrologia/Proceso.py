import os
import pandas as pd
import sys
import re
reload(sys)
sys.setdefaultencoding('utf-8')

data = pd.read_csv(r'C:\Users\marlon.ruiz\Downloads\pandas.txt', delimiter = ',',dtype={'MpCodigo':str})
folder = r"\\172.26.0.20\SubAgrologia\Datos_Abiertos\DATOS_ABIERTOS_2022\AHT"
#folder_salida = r"\\172.26.0.20\SubAgrologia\Datos_Abiertos\DATOS_ABIERTOS_2022\AHT\1_PUBLICACION"
folder_salida = u"D:\gdb"
lista = []
for path, directories, files in os.walk(folder):
    for name in files:
        if name.endswith(".mdb"):
            try:
                #print(os.path.join(path,name)+"\t--\n"+name[4:])
                lista.append(name)
                #arcpy.ExportXMLWorkspaceDocument_management(os.path.join(folder_salida,name), os.path.join(folder_salida,name[:-4]+".xml"), "SCHEMA_ONLY", "BINARY", "METADATA")
                #arcpy.CreateFileGDB_management(path,name[:-4] + ".gdb")
                
            except:
                next
lista1 = []
for i in lista:
    print(i)
    if len(i.split("_"))<=2:
	    print("entra")
	    lista1.append(i.split("_"))

df1 = pd.DataFrame(lista1).rename(columns={0:'divipola',1:'anio'})
df1['mdb'] = df1['divipola']+"_"+df1['anio']

df = pd.merge(df1,data,left_on='divipola',right_on='MpCodigo')

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
df['Departamento'] = df['Depto'].apply(remove_accents)
