"""
Script de validación de productos geodesicos
Author: Subdirección cartográfia y geodesia - IGAC
        Marlon Ruiz
"""
import os
import time
import pandas as pd
import arcpy

def ReadExcel(listaExcel):
    appended_data = []
    for i in listaExcel:
        try:
            df = pd.read_excel(i)
            appended_data.append(df)
        except:
            pass
    # see pd.concat documentation for more info
    appended_data = pd.concat(appended_data)
    return appended_data

def CompileData(daf):
    #arcpy.AddMessage(daf)
    imagen = []
    desc = []
    pto = []
    for index, row in daf.iterrows():
        if row['Imagenes'].endswith("_1"):
            imagen.append(row['Imagenes'])
            desc.append('Perfil')
            pto.append(row['Imagenes'].replace("_1", ""))
        elif row['Imagenes'].endswith("_2"):
            imagen.append(row['Imagenes'])
            desc.append('Croquis detallado')
            pto.append(row['Imagenes'].replace("_2", ""))
        elif row['Imagenes'].endswith("_3"):
            imagen.append(row['Imagenes'])
            desc.append('Croquis general')
            pto.append(row['Imagenes'].replace("_3", ""))
        elif row['Imagenes'].endswith("_4"):
            imagen.append(row['Imagenes'])
            desc.append('Imagen placa')
            pto.append(row['Imagenes'].replace("_4", ""))
        elif row['Imagenes'].endswith("_5"):
            imagen.append(row['Imagenes'])
            desc.append('Diagrama de Obstaculos')
            pto.append(row['Imagenes'].replace("_5", ""))
        else:
            imagen.append(row['Imagenes'])
            desc.append('No estandarizado')
            pto.append(row['Imagenes'])
    dfin= pd.DataFrame(list(zip(pto,imagen,desc)),columns =['Vertice','Imagen','Descripcion'])
    return dfin
    
def ExportExcel(param1,data_frame1,data_frame2):
    # create a excel writer object
    #data_frame1 = data_frame1.applymap(lambda x: x.encode('unicode_escape').decode('utf-8') if isinstance(x, str) else x)
    #arcpy.AddMessage(data_frame1.head())
    #arcpy.AddMessage(data_frame2.head())
    data_frame1.to_csv(os.path.join(param1,'Reporte.txt'),sep='|',encoding='utf-8-sig')
    arcpy.AddMessage('****************Exportado el reporte')
    data_frame2.to_csv(os.path.join(param1,'Duplicados.txt'),sep='|',encoding='utf-8-sig')
    arcpy.AddMessage('****************Exportado duplicados')
    '''
    with pd.ExcelWriter(os.path.join(param1,'Reporte.xlsx'), engine='xlsxwriter') as writer:
        # use to_excel function and specify the sheet_name and index
        # to store the dataframe in specified sheet
        data_frame1.to_excel(writer, sheet_name="Resumen", index=False)
        data_frame2.to_excel(writer, sheet_name="Duplicados", index=False)'''
    arcpy.AddMessage('Archivos guardados con exito')
        
def ScriptTool(param0, param1):
    # Script execution code goes here
    """Se realiza el mapeo de la carpeta de acuerdo con las imagenes en formato jpg y los excel de las entregas"""
    fecha = []
    listaraster=[]
    imagenes = []
    listaExcel = []
    arcpy.AddMessage('Se empieza el mapeo del directorio... Esto puede tardar unos minutos')
    for path, directories, files in os.walk(param0):
        for name in files:
            try:
                if name.endswith((".JPG",".jpg")):
                    Rutaraster=os.path.join(path,name)
                    fecha.append(time.strftime('%d/%m/%Y', time.gmtime(os.path.getmtime(Rutaraster))))
                    listaraster.append(Rutaraster)
                    imagenes.append(name)
                elif name.endswith((".xls",".xlsx")):
                    excel=os.path.join(path,name)
                    listaExcel.append(excel)
            except FileNotFoundError:
                next
    arcpy.AddMessage('Fin del Mapeo')
    arcpy.AddMessage('Se econtraron {0} imagenes y {1} archivos de Excel dentro del directorio raíz'.format(len(listaraster), len(listaExcel)))
    df = pd.DataFrame(list(zip(imagenes,fecha,listaraster)),columns =['Imagenes', 'Fecha','Ruta'])
    df['Imagenes']=df['Imagenes'].replace(['.JPG','.jpg'],'', regex=True)
    arcpy.AddMessage('**********************************************************************************************************************')
    arcpy.AddMessage('*****************************Dataframe de todas las imagenes en el directorio******************************************')
    arcpy.AddMessage(df)
    arcpy.AddMessage('**********************************************************************************************************************')
    arcpy.AddMessage('**********************************************************************************************************************')
    df1 = CompileData(df)
    arcpy.AddMessage('**********************************************************************************************************************')
    arcpy.AddMessage('*****************************Dataframe de la compilación de las descripciones****************************************')
    arcpy.AddMessage(df1)
    arcpy.AddMessage('**********************************************************************************************************************')
    arcpy.AddMessage('**********************************************************************************************************************')
    df1 = df1.merge(df, left_on='Imagen', right_on='Imagenes')
    df1.set_index("Vertice", inplace = True)
    df1 = df1.pivot_table(index='Vertice', columns='Descripcion', values='Ruta', aggfunc=lambda x: ' '.join(x))
    arcpy.AddMessage(df1)
    df2 = ReadExcel(listaExcel)
    duplicados = df2[df2.duplicated()]
    arcpy.AddMessage('**********************************************************************************************************************')
    arcpy.AddMessage('Se generan los valores duplicados a examinar')
    arcpy.AddMessage('**********************************************************************************************************************')
    df2 = df2[df2.duplicated()==False]
    export = df2.merge(df1, left_on='Nomenclatura Estandarizada', right_on='Vertice', how='left')
    arcpy.AddMessage('**********************************************************************************************************************')
    arcpy.AddMessage('Exportando el archivo excel en la ruta:\n {0}'.format(str(param1)))
    arcpy.AddMessage('**********************************************************************************************************************')
    ExportExcel(param1,export,duplicados)
    return

'''def ScriptTool(param0, param1):
    # Script execution code goes here
    MappingFolder(param0)
    return'''

# This is used to execute code if the file was run but not imported
if __name__ == '__main__':

    # Tool parameter accessed with GetParameter or GetParameterAsText
    param0 = arcpy.GetParameterAsText(0)
    param1 = arcpy.GetParameterAsText(1)
    
    ScriptTool(param0, param1)
