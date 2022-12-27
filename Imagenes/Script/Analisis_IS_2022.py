"""Este script permite extraer informacion de la imagen y sus metadatos y consolidarla en un excel:
  --directorio: Ruta de la carpeta en donde se encuentra(n) la(s) imagen(es) a analizar
  --rutasalida: Ruta donde se guardan los resultados.
  --sensor: Sensor de las imagenes a analizar
  El resultado obtenido es un excel que indica datos relacionados con la imagen, una capa del footprint de la imagen y una capa de nubes de las imagenes 
  Autor: Maycol Zaraza
   """
import arcpy
import random
from arcpy import env
from arcpy.sa import *
import os
import requests
import time
import argparse
import sys
import time
from datetime import datetime
from xlrd import open_workbook
import xlwt
from xml.dom import minidom
import json
import glob
"""
if __name__ == "__main__":
 arcpy.CheckOutExtension("spatial")
 parser = argparse.ArgumentParser(description='Validador Datos de Imagenes - IGAC')
 parser.add_argument('--directorio', type=str, help="e.g. C:\Imagenes\PlanetScope\Fuente")
 parser.add_argument('--rutasalida', type=str, help="e.g. C:\Imagenes\PlanetScope\Resultados")
 parser.add_argument('--sensor', type=str, help="e.g. PlanetScope")
 parser.add_argument('--vfiltro', type=int, help="e.g. 240")
 # In case any parameter is passed
 args = parser.parse_args()
 directorio = "C:\Imagenes\PlanetScope\Fuente" if not args.directorio else args.directorio
 rutasalida = "C:\Imagenes\PlanetScope\Resultados" if not args.rutasalida else args.rutasalida
 sensor = "PlanetScope" if not args.sensor else args.sensor
 vfiltro = 240 if not args.vfiltro else args.vfiltro
"""
directorio = arcpy.GetParameterAsText(0)
rutasalida = arcpy.GetParameterAsText(1)
sensor = arcpy.GetParameterAsText(2)
vfiltro = arcpy.GetParameterAsText(3)
sensores = {'PLANETSCOPE':['_1B_AnalyticMS','tif'], 'PLANETNICFI':['_3B_AnalyticMS_SR','tif'],'PLEIADES':['XML'], 'GEOEYE':['TIL'], 'SKYSAT':['_analytic','tif'], 'WORLDVIEW':['TIL'], 'IKONOS':['tif'], 'QUICKBIRD':['TIL'], 'RAPIDEYE':['ntf'], 'ALOS':['img'], 'ASTER':['img'], 'CBERS':['img'], 'DMC':['tif'], 'KOMPSAT':['tif'], 'WORLDVIEWOT':['_SEAMLINES_SHAPE','tif','sid'], 'GEOEYEOT':['_SEAMLINES_SHAPE','tif','sid']}
nowd = datetime.now()
#Crear excel resumen
style0 = xlwt.easyxf('font: name Arial, colour black, bold on, height 220;''align: horiz center')
style1 = xlwt.easyxf('font: name Arial, colour black, height 220;''align: horiz center')
wbrv = xlwt.Workbook()
wsrv = wbrv.add_sheet('EVAL',cell_overwrite_ok=True)
#wsrv.write(0, 0, 'Estructura e Integridad', style0)
wsrv.write(0, 0, 'IMAGEN/ID', style0)
wsrv.write(0, 1, 'Departamento', style0)
wsrv.write(0, 2, 'Municipio', style0)
wsrv.write(0, 3, 'RESOLUCION ESPACIAL (m)', style0)
wsrv.write(0, 4, 'RESOLUCION ESPECTRAL', style0)
wsrv.write(0, 5, 'RESOLUCION RADIOMETRICA', style0)
wsrv.write(0, 6, 'SISTEMA DE REFERENCIA', style0)
wsrv.write(0, 7, 'RESOLUCION TEMPORAL', style0)
wsrv.write(0, 8, 'AREA (ha)', style0)
wsrv.write(0, 9, 'AREA NUBES (ha)', style0)
wsrv.write(0, 10, 'NUBOSIDAD (%)', style0)
wsrv.write(0, 11, 'RUTA', style0)
wsrv.write(0, 12, 'NIVEL DE PROCESAMIENTO', style0)
wsrv.write(0, 13, 'ANGULO DE INCIDENCIA, OFF NADIR', style0)
#Configurar esta ruta segun donde se ubique el script
#dtos = "C:\Users\maycol.zaraza\Documents\Prueba_Img\Dtos_Mpios\Dptosprj.shp"
#mpios = "C:\Users\maycol.zaraza\Documents\Prueba_Img\Dtos_Mpios\Mpios.shp"
#dtos = r"\\172.26.0.20\Elite_Sub_Geografia_Cartografia\3080GITLimites\79RLimites\1BDGeografica\Limites_Entidades_Territoriales_Junio_2021.gdb\Limites_Entidades_Territoriales\Depto"
#mpios = r"\\172.26.0.20\Elite_Sub_Geografia_Cartografia\3080GITLimites\79RLimites\1BDGeografica\Limites_Entidades_Territoriales_Junio_2021.gdb\Limites_Entidades_Territoriales\Munpio"
dtos = arcpy.GetParameterAsText(4)
mpios = arcpy.GetParameterAsText(5)
#dirs = os.listdir(directorio)
dirs = [ name for name in os.listdir(directorio) if os.path.isdir(os.path.join(directorio, name)) ]
salidanub = rutasalida+"\AreaNubes.shp"
spatial_reference = arcpy.Describe(dtos).spatialReference
#Capa de Nubes
arcpy.CreateFeatureclass_management(rutasalida, "AreaNubes.shp", "POLYGON","","","",spatial_reference)
arcpy.AddField_management(salidanub, "Imagen_ID", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidanub, "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
#Capa de Footprint
salidafoot = rutasalida+"\Footprint.shp"
arcpy.CreateFeatureclass_management(rutasalida, "Footprint.shp", "POLYGON","","","",spatial_reference)
arcpy.AddField_management(salidafoot, "Imagen_ID", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Dpto", "TEXT", "", "", 250, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Mpio", "TEXT", "", "", 250, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "R_esp", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "R_espc", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "R_radiom", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Sistema_R", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "R_Temp", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "AreaNub_ha", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Prc_Nub", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Ruta", "TEXT", "", "", 250, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Nivel_P", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
arcpy.AddField_management(salidafoot, "Ang_inc", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
def crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot):
  #Cruce Dtos y Mpios
  arcpy.AddMessage('Cruzando con Dptos y Mpios')
  arcpy.MakeFeatureLayer_management (dtos, "departamento")
  inFeatures_pcd = ["departamento", salidaftp]
  outName_pcd = rutasalida + "\\" + 'Areadpto_'+file.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_pcd, outName_pcd)
  arcpy.MakeFeatureLayer_management (outName_pcd, "areadpto")
  arcpy.AddField_management("areadpto", "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management("areadpto", "Area_ha", exp, "PYTHON3")
  out_sort =  rutasalida + "\\" + 'Areadptoso_'+file.replace('-','')+'.shp'
  arcpy.Sort_management("areadpto", out_sort, [["Area_ha", "DESCENDING"]])
  arcpy.MakeFeatureLayer_management (out_sort, "areadptos")
  #arcpy.SelectLayerByLocation_management("departamento", "intersect", outName_intp)
  cursor = arcpy.da.SearchCursor('areadptos', ['DeNombre','Area_ha'])
  nombredepto = []
  for row in cursor:
    nombredepto.append(("{0}".format(row[0].encode('UTF-8'))))
  nombredepto_str = ''
  for n in nombredepto:
    nombredepto_str += str(n) + ", "
  nombredepto_str = str(nombredepto_str[:-2].encode('UTF-8'), "windows-1252")
  #wsrv.write(j,1,nombredepto_str.capitalize())
  exp = '"'+nombredepto_str+'"'
  arcpy.CalculateField_management(salidaftp, "Dpto", exp, "PYTHON3")
  arcpy.Delete_management("departamento")
  arcpy.Delete_management("areadpto")
  arcpy.Delete_management("areadptos")
  arcpy.Delete_management(outName_pcd)
  arcpy.Delete_management(out_sort)
  arcpy.MakeFeatureLayer_management (mpios, "municipios")
  inFeatures_pcm = ["municipios", salidaftp]
  outName_pcm = rutasalida + "\\" + 'Areampio_'+file.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_pcm, outName_pcm)
  arcpy.MakeFeatureLayer_management (outName_pcm, "areampio")
  arcpy.AddField_management("areampio", "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management("areampio", "Area_ha", exp, "PYTHON3")
  out_sort =  rutasalida + "\\" + 'Areampios_'+file.replace('-','')+'.shp'
  arcpy.Sort_management("areampio", out_sort, [["Area_ha", "DESCENDING"]])
  arcpy.MakeFeatureLayer_management (out_sort, "areampios")
  #arcpy.SelectLayerByLocation_management("municipios", "intersect", outName_intp)
  cursormunicipio = arcpy.da.SearchCursor('areampios', ['MpNombre','Area_ha'])
  nombremunipio = []
  for row in cursormunicipio:
    nombremunipio.append(("{0}".format(row[0].encode('UTF-8'))))
  nombremunipio_str = ''
  for n in nombremunipio:
    nombremunipio_str += str(n) + ", "
  nombremunipio_str = str(nombremunipio_str[:-2].encode('UTF-8'), "windows-1252")
  #wsrv.write(j,2,nombremunipio_str.capitalize())
  exp = '"'+nombremunipio_str+'"'
  arcpy.CalculateField_management(salidaftp, "Mpio", exp, "PYTHON3")
  arcpy.Append_management(salidaftp, salidafoot, "NO_TEST","","")
  arcpy.Delete_management("municipios")
  arcpy.Delete_management("areampio")
  arcpy.Delete_management("areampios")
  arcpy.Delete_management(outName_pcm)
  arcpy.Delete_management(out_sort)
  arcpy.Delete_management(salidaftp)
  return nombredepto_str, nombremunipio_str
def resexcel(wsrv,rasterObj,style1,j,sensor):
  arcpy.AddMessage('Extrayendo resoluciones')
  respectral = rasterObj.bandCount
  rradiom = rasterObj.pixelType
  respacial = rasterObj.meanCellWidth
  srfespacial = rasterObj.spatialReference.name
  #wsrv.write(j, 0, file + ext, style1)
  if(sensor == 'ASTER'):
    respacial = respacial*100000
  wsrv.write(j, 3, round(respacial,2), style1)
  wsrv.write(j, 4, respectral, style1)
  wsrv.write(j, 5, rradiom, style1)
  wsrv.write(j, 6, srfespacial, style1)
  #wsrv.write(j, 11, imagen, style1)
  return respectral,rradiom,round(respacial,2),srfespacial
    
def masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro):
  #Nubes
  #Leer Imagen
  desc = arcpy.Describe(rasterObj)
  nband1 = desc.children[0].name
  band1 = imagen+"\\"+nband1
  arcpy.AddMessage('Generando Banda 1 para su filtrado')
  image_band_1_out = os.path.join(rutasalida, file +'_band_1.tif')
  arcpy.CopyRaster_management(band1,image_band_1_out)
  arcpy.AddMessage(str(image_band_1_out)) #1 punto
  banda1 = arcpy.Raster(image_band_1_out)
  arcpy.AddMessage(str(banda1)) #2 punto
  filtim = banda1 > int(vfiltro)
  arcpy.AddMessage('Filtrando nubes para su cuantificacion')
  attExtract = ExtractByAttributes(filtim, "VALUE =1")
  salidanubim = rutasalida+"\AreaNubes1.shp"
  #Conversion a Poligono
  arcpy.RasterToPolygon_conversion(attExtract, salidanubim , "NO_SIMPLIFY","VALUE")
  #Campo de Area
  arcpy.AddField_management(salidanubim, "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management(salidanubim, "Area_ha", exp, "PYTHON3")
  #Campo de Nombre
  arcpy.AddField_management(salidanubim, "Imagen_ID", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
  exp2 = '"'+file + ext+'"'
  arcpy.CalculateField_management(salidanubim, "Imagen_ID", exp2, "PYTHON3")
  salidatb = rutasalida + "\\tabla_" + file[0:5]+".dbf"
  arcpy.AddMessage('Esta entrando aca'+str(salidatb)) #3 punto
  arcpy.Statistics_analysis(salidanubim, salidatb, [["Area_ha", "SUM"]])
  field_names = [i.name for i in arcpy.ListFields(salidatb) if i.type != 'OID']
  cursor = arcpy.da.SearchCursor(salidatb, field_names)
  data=[row for row in cursor]
  if data == []:
    arcpy.AddMessage('No se generaron registros filtrados en areas de nubosidad')
    areanubes = 0
  else:
    areanubes = data[0][1]
    arcpy.AddMessage('El area por nubosidad es: '+str(areanubes))
  #wsrv.write(j, 9, round(areanubes,3), style1)
  arcpy.Append_management(salidanubim, salidanub, "NO_TEST","","")
  arcpy.Delete_management(salidatb)
  #arcpy.Delete_management(image_band_1_out)
  arcpy.Delete_management(salidanubim)
  return areanubes, banda1, image_band_1_out
def footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor):
  #Footprint
  arcpy.AddMessage('Generando footprint imagen')
  if(sensor == "CBERS"):
    filtim2 = banda1 > 1
  else:
    filtim2 = banda1 > 0
  attExtract2 = ExtractByAttributes(filtim2, "VALUE =1")
  salidaftp = rutasalida+"\\footp"+file.replace('-','')+".shp"
  arcpy.RasterToPolygon_conversion(attExtract2, salidaftp , "NO_SIMPLIFY","VALUE")
  arcpy.AddField_management(salidaftp, "Imagen_ID", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+file + ext+'"'
  arcpy.CalculateField_management(salidaftp, "Imagen_ID", exp, "PYTHON3")
  result = arcpy.GetCount_management(salidaftp)
  count = int(result.getOutput(0))
  #arcpy.AddMessage('Numero elementos', count)
  if count>1:
    salidaftp2 = rutasalida+"\\footp2"+file.replace('-','')+".shp"
    dissolveFields = ["Imagen_ID"]
    arcpy.Dissolve_management(salidaftp, salidaftp2, dissolveFields, "", "MULTI_PART", "DISSOLVE_LINES")
    arcpy.Delete_management(salidaftp)
    salidaftp = salidaftp2
  arcpy.AddField_management(salidaftp, "Dpto", "TEXT", "", "", 250, "", "NULLABLE", "NON_REQUIRED")
  arcpy.AddField_management(salidaftp, "Mpio", "TEXT", "", "", 250, "", "NULLABLE", "NON_REQUIRED")
  arcpy.AddField_management(salidaftp, "R_esp", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+str(respacial)+'"'
  arcpy.CalculateField_management(salidaftp, "R_esp", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "R_espc", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+str(respectral)+'"'
  arcpy.CalculateField_management(salidaftp, "R_espc", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "R_radiom", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+str(rradiom)+'"'
  arcpy.CalculateField_management(salidaftp, "R_radiom", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "Sistema_R", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+str(srfespacial)+'"'
  arcpy.CalculateField_management(salidaftp, "Sistema_R", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "R_Temp", "TEXT", "", "", 100, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+str(res_temporal)+'"'
  arcpy.CalculateField_management(salidaftp, "R_Temp", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management(salidaftp, "Area_ha", exp, "PYTHON3")
  salidaft = rutasalida + "\\tftp" + file[0:5]+".dbf" #Punto 4
  arcpy.Statistics_analysis(salidaftp, salidaft, [["Area_ha", "SUM"]])
  field_names = [i.name for i in arcpy.ListFields(salidaft) if i.type != 'OID']
  cursor = arcpy.da.SearchCursor(salidaft, field_names)
  data=[row for row in cursor]
  if data == []:
    arcpy.AddMessage('La imagen no tiene informacion')
    areaimagen = 0
  else:
    areaimagen = data[0][1]
    arcpy.AddMessage('El area de la imagen es '+str(areaimagen))
  #wsrv.write(j, 8, round(areaimagen,3), style1)
  arcpy.AddField_management(salidaftp, "AreaNub_ha", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  exp = str(areanubes)
  arcpy.CalculateField_management(salidaftp, "AreaNub_ha", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "Prc_Nub", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  prcnub = round((float(areanubes)/float(areaimagen))*100,2)
  #wsrv.write(j, 10, round(prcnub,2), style1)
  arcpy.AddMessage('El porcentaje de area nubosidad es '+str(prcnub)+ ' %')
  exp = str(prcnub)
  arcpy.CalculateField_management(salidaftp, "Prc_Nub", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "Ruta", "TEXT", "", "", 1000, "", "NULLABLE", "NON_REQUIRED")
  arcpy.AddMessage(str(imagen))
  exp = "r'"+str(imagen)+"'"
  arcpy.CalculateField_management(salidaftp, "Ruta", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "Nivel_P", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  exp = '"'+nivel_pr+'"'
  arcpy.CalculateField_management(salidaftp, "Nivel_P", exp, "PYTHON3")
  arcpy.AddField_management(salidaftp, "Ang_inc", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED")
  exp = str(ang_incidencia)
  arcpy.CalculateField_management(salidaftp, "Ang_inc", exp, "PYTHON3")
  arcpy.Delete_management(salidaft)
  arcpy.Delete_management(image_band_1_out)
  
  return areaimagen, prcnub, salidaftp
def leerxml(rutaxml,adq,tipopr,ang_in):
  doc = minidom.parse(rutaxml)
  res_temporal = doc.getElementsByTagName(adq)[0].firstChild.data
  nivel_pr = doc.getElementsByTagName(tipopr)[0].firstChild.data
  ang_incidencia = doc.getElementsByTagName(ang_in)[0].firstChild.data
  
  return res_temporal, nivel_pr, ang_incidencia
def leerjson(rutajson,adq,tipopr,ang_in):
  with open(rutajson) as file:
    data = json.load(file)
  res_temporal = data['properties'][adq]
  nivel_pr = data['properties'][tipopr]
  ang_incidencia = data['properties'][ang_in]
  
  return res_temporal, nivel_pr, ang_incidencia
j = 0
for file in dirs:
  j+=1
  ndir = directorio + "\\" + file
  env.workspace = ndir
  if(sensor == 'PLANETSCOPE'):
    arcpy.AddMessage('Imagen numero '+str(j))
    rasterList = arcpy.ListRasters()
    ext = sensores[sensor][0]
    formato = sensores[sensor][1]
    imagen = ndir + "\\" + file + ext + "."+formato
    imagenpr = ndir + "\\imagen_proy.tif"
    arcpy.ProjectRaster_management(imagen, imagenpr, spatial_reference, "BILINEAR")
    rasterObj = arcpy.Raster(imagenpr)
    arcpy.AddMessage('Analizando la imagen '+ file + ext)
    wsrv.write(j, 0, file + ext, style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer XML
    arcpy.AddMessage('Leyendo Archivo metadatos')
    rutaxml = ndir + "\\" + file + ext + "_metadata.xml"
    res_temporal, nivel_pr, ang_incidencia = leerxml(rutaxml,"eop:acquisitionDate","eop:productType","eop:incidenceAngle")
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    doc = minidom.parse(rutaxml)
    respacial = round(float(doc.getElementsByTagName("ps:rowGsd")[0].firstChild.data),2)
    wsrv.write(j, 3, respacial, style1)
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagenpr,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagenpr,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.Delete_management(imagenpr)
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  if(sensor == 'PLANETNICFI'):
    arcpy.AddMessage('Imagen numero '+str(j))
    filesd = [ name for name in os.listdir(ndir) if os.path.isdir(os.path.join(ndir, name)) ] #os.listdir(ndir)
    ndir_prd = ndir + "\\" + filesd[0]
    env.workspace = ndir_prd
    rasterList = arcpy.ListRasters()
    ext = sensores[sensor][0]
    formato = sensores[sensor][1]
    imagen = ndir_prd + "\\" + file + ext + "."+formato
    rasterObj = arcpy.Raster(imagen)
    arcpy.AddMessage('Analizando la imagen '+ file + ext)
    wsrv.write(j, 0, file + ext, style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer XML
    arcpy.AddMessage('Leyendo Archivo metadatos')
    rutaxml = ndir_prd + "\\" + file + ext[:-3] + "_metadata.xml"
    res_temporal, nivel_pr, ang_incidencia = leerxml(rutaxml,"eop:acquisitionDate","eop:productType","eop:incidenceAngle")
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    doc = minidom.parse(rutaxml)
    respacial = round(float(doc.getElementsByTagName("ps:rowGsd")[0].firstChild.data),2)
    wsrv.write(j, 3, respacial, style1)
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'PLEIADES'):
    filesd = [ name for name in os.listdir(ndir) if os.path.isdir(os.path.join(ndir, name)) ] #os.listdir(ndir)
    arcpy.AddMessage('Analizando la imagen '+ str(file))
    arcpy.AddMessage('Imagen numero '+str(j))
    ext = sensores[sensor][0]
    filesd.sort()
    ndir_prd = ndir + "\\" + filesd[0]
    env.workspace = ndir_prd
    rasterList = arcpy.ListRasters("*", ext)
    imagen = ndir_prd + "\\" + rasterList[0]
    imagenpr = ndir_prd + "\\imagen_proy.tif"
    arcpy.ProjectRaster_management(imagen, imagenpr, spatial_reference, "BILINEAR")
    rasterObj = arcpy.Raster(imagenpr)
    
    wsrv.write(j, 0, rasterList[0], style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer XML
    arcpy.AddMessage('Leyendo Archivo metadatos')
    rutaxml = glob.glob(ndir_prd + "/DIM*.XML")
    #rutaxml = ndir_prd + "\\" + rasterList[0].split('.')[0] + ".XML"
    res_temporal, nivel_pr, ang_incidencia = leerxml(rutaxml[0],"PRODUCTION_DATE","RADIOMETRIC_PROCESSING","INCIDENCE_ANGLE")
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    file = rasterList[0].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagenpr,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagenpr,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.Delete_management(imagenpr)
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'GEOEYE' or sensor == 'WORLDVIEW' or sensor == 'QUICKBIRD'):
    filesd = os.listdir(ndir)
    arcpy.AddMessage('Analizando la imagen '+ str(file))
    arcpy.AddMessage('Imagen numero '+str(j))
    ext = sensores[sensor][0]
    filesd.sort()
    ndir_pan = ndir + "\\" + filesd[1]
    env.workspace = ndir_pan
    rasterList = arcpy.ListRasters("*", "TIL")
    imagen = ndir_pan + "\\" + rasterList[0]
    rasterObj = arcpy.Raster(imagen)
    respacial = rasterObj.meanCellWidth
    wsrv.write(j, 3, round(respacial,2), style1)
    ndir_mul = ndir + "\\" + filesd[0]
    env.workspace = ndir_mul
    rasterList = arcpy.ListRasters("*", "TIL")
    imagen = ndir_mul + "\\" + rasterList[0]
    imagenpr = ndir_mul + "\\imagen_proy.tif"
    arcpy.ProjectRaster_management(imagen, imagenpr, spatial_reference, "BILINEAR")
    rasterObj = arcpy.Raster(imagenpr)
    respectral = rasterObj.bandCount
    rradiom = rasterObj.pixelType
    srfespacial = rasterObj.spatialReference.name
    wsrv.write(j, 4, respectral, style1)
    wsrv.write(j, 5, rradiom, style1)
    wsrv.write(j, 6, srfespacial, style1)
    wsrv.write(j, 0, rasterList[0], style1)
    wsrv.write(j, 11, imagen, style1)
    #respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer XML
    arcpy.AddMessage('Leyendo Archivo metadatos')
    rutaxml = ndir_mul + "\\" + rasterList[0].split('.')[0] + ".XML"
    res_temporal, nivel_pr, ang_incidencia = leerxml(rutaxml,"FIRSTLINETIME","PRODUCTLEVEL","MAXOFFNADIRVIEWANGLE")
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    file = rasterList[0].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagenpr,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagenpr,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.Delete_management(imagenpr)
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'GEOEYEOT' or sensor == 'WORLDVIEWOT'):
    arcpy.AddMessage('Analizando la imagen '+str(file))
    arcpy.AddMessage('Imagen numero '+str(j))
    ext = sensores[sensor][0]
    formato = sensores[sensor][1]
    rasterList = arcpy.ListRasters("*R*C*", formato)[1:]
    formato = sensores[sensor][2]
    rasterList.extend(arcpy.ListRasters("*R*C*", formato)[1:])
    if rasterList == []:
      arcpy.AddMessage("No hay imagenes")
    else:
      arcpy.AddMessage("Realizando mosaico")
      output = file + "_mosaic.tif"
      vt5 = arcpy.ValueTable()
      for raster in rasterList:
        rasterObj = arcpy.Raster(raster)
        arcpy.AddMessage(raster)
        vt5.addRow(rasterObj)
      arcpy.MosaicToNewRaster_management(vt5,ndir,output,"PROJCS['WGS_1984_UTM_Zone_18N',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['false_easting',500000.0],PARAMETER['false_northing',0.0],PARAMETER['central_meridian',-75.0],PARAMETER['scale_factor',0.9996],PARAMETER['latitude_of_origin',0.0],UNIT['Meter',1.0]]","8_BIT_UNSIGNED","0.5","3","FIRST")
      arcpy.AddMessage("Mosaico "+output+" Realizado")
    imagen = ndir + "\\" + output
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, file, style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer SHP Metadados
    arcpy.AddMessage('Leyendo Archivo metadatos')
    namecshp = file + ext
    rutashp = ndir + "\\" + namecshp + "\\"+namecshp+".shp"
    cursor = arcpy.da.SearchCursor(rutashp, ["acquisitio","productTyp","offNadirAn"])
    data=[row for row in cursor]
    res_temporal = data[0][0]
    nivel_pr = data[0][1]
    ang_incidencia = data[0][2]
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    ext = ""
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'IKONOS'):
    filesd = os.listdir(ndir)
    arcpy.AddMessage('Imagen numero '+str(j))
    arcpy.AddMessage('Analizando la imagen '+str(file))
    ndir_p = ndir + "\\" + filesd[0]
    env.workspace = ndir_p
    ext = sensores[sensor][0]
    rasterList = arcpy.ListRasters("*", ext)
    #formato = sensores[sensor][1]
    rasterList.sort()
    imagen = ndir_p + "\\" + rasterList[1]
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, file, style1)
    wsrv.write(j, 11, imagen, style1)
    respacial = rasterObj.meanCellWidth
    respectral = rasterObj.bandCount
    rradiom = rasterObj.pixelType
    srfespacial = rasterObj.spatialReference.name
    wsrv.write(j, 3, round(respacial,2), style1)
    wsrv.write(j, 4, respectral, style1)
    wsrv.write(j, 5, rradiom, style1)
    wsrv.write(j, 6, srfespacial, style1)
    #Leer JSON
    arcpy.AddMessage('Leyendo Archivo metadatos')
    ruta = rasterList[1].split('.')[0].split("_")
    rnew = ruta[:-2]
    sep = "_"
    rutanueva = sep.join(rnew)
    txtdrv = ndir_p + "\\" + rutanueva + "_metadata.txt"
    f = open(txtdrv, "r")
    content = f.read()
    #Extraer punto
    rt = content.find("Date/Time")
    npr = content.find("Processing Level")
    ai = str(0)
    res_temporal = content[rt+len("Date/Time")+2:rt+len("Date/Time")+18]
    nivel_pr = content[npr+len("Processing Level")+2:npr+len("Processing Level")+34]
    ang_incidencia = ai
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    ext= " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'SKYSAT'):
    arcpy.AddMessage('Imagen numero '+str(j))
    rasterList = arcpy.ListRasters()
    ext = sensores[sensor][0]
    formato = sensores[sensor][1]
    imagen = ndir + "\\" + file + ext + "."+formato
    rasterObj = arcpy.Raster(imagen)
    arcpy.AddMessage('Analizando la imagen '+ str(file + ext))
    wsrv.write(j, 0, file + ext, style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer JSON
    arcpy.AddMessage('Leyendo Archivo metadatos')
    rutajson = ndir + "\\" + file + "_metadata.json"
    res_temporal, nivel_pr, ang_incidencia = leerjson(rutajson,"acquired","quality_category","view_angle")
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'RAPIDEYE'):
    arcpy.AddMessage('Imagen numero '+str(j))
    arcpy.AddMessage('Analizando la imagen '+str(file))
    env.workspace = ndir
    ext = sensores[sensor][0]
    rasterList = arcpy.ListRasters("*", ext)
    #formato = sensores[sensor][1]
    imagen = ndir + "\\" + rasterList[0]
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, file, style1)
    wsrv.write(j, 11, imagen, style1)
    respacial = rasterObj.meanCellWidth
    respectral = rasterObj.bandCount
    rradiom = rasterObj.pixelType
    srfespacial = rasterObj.spatialReference.name
    wsrv.write(j, 3, round(respacial,2), style1)
    wsrv.write(j, 4, 5, style1)
    wsrv.write(j, 5, rradiom, style1)
    wsrv.write(j, 6, srfespacial, style1)
    #Leer JSON
    arcpy.AddMessage('Leyendo Archivo metadatos')
    ruta = rasterList[0].split('.')[0].split("_")
    rnew = ruta[:-1]
    sep = "_"
    rutanueva = sep.join(rnew)
    rutaxml = ndir + "\\" + rutanueva + "_metadata.xml"
    res_temporal, nivel_pr, ang_incidencia = leerxml(rutaxml,"re:startDateTime","eop:productType","eop:incidenceAngle")
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    ext= " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'ALOS'):
    filesd = os.listdir(ndir)
    arcpy.AddMessage('Analizando la imagen '+ str(file))
    arcpy.AddMessage('Imagen numero '+str(j))
    ext = sensores[sensor][0]
    ndir_prd = ndir + "\\" + filesd[0]
    env.workspace = ndir_prd
    rasterList = arcpy.ListRasters("*", ext)
    imagen = ndir_prd + "\\" + rasterList[0]
    rasterObj = arcpy.Raster(imagen)
    
    wsrv.write(j, 0, rasterList[0], style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer TXT
    arcpy.AddMessage("Leyendo txt..")
    txtdrv = ndir_prd + "\\" + rasterList[0].split('.')[0] + ".txt"
    f = open(txtdrv, "r")
    content = f.read()
    #Extraer punto
    rt = content.find("Rst_AV2_WkrepStartTime")
    npr = content.find("Img_SceneCenterAngle")
    ai = content.find("Img_PointingAngle")
    res_temporal = content[rt+len("Rst_AV2_WkrepStartTime")+2:rt+len("Rst_AV2_WkrepStartTime")+19]
    nivel_pr = content[npr+len("Img_SceneCenterAngle")+2:npr+len("Img_SceneCenterAngle")+6]
    ang_incidencia = content[ai+len("Img_PointingAngle")+2:ai+len("Img_PointingAngle")+7]
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    
    file = rasterList[0].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'ASTER'):
    arcpy.AddMessage('Imagen numero '+str(j))
    arcpy.AddMessage('Analizando la imagen '+str(file))
    env.workspace = ndir
    ext = sensores[sensor][0]
    rasterList = arcpy.ListRasters("*", ext)
    #formato = sensores[sensor][1]
    rasterList.sort()
    imagen = ndir + "\\" + rasterList[0]
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, rasterList[0], style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer MET
    arcpy.AddMessage('No se puede leer el metadato .Met')
    ruta = rasterList[0].split('.')[0].split("_")
    
    res_temporal = ruta[3]
    
    # res_temporal = ""
    nivel_pr = "L1A"
    ang_incidencia = "0"
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    file = rasterList[0].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'CBERS'):
    arcpy.AddMessage('Imagen numero '+str(j))
    arcpy.AddMessage('Analizando la imagen '+str(file))
    env.workspace = ndir
    ext = sensores[sensor][0]
    rasterList = arcpy.ListRasters("*", ext)
    #formato = sensores[sensor][1]
    rasterList.sort()
    imagen = ndir + "\\" + rasterList[1]
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, rasterList[1], style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer MET
    arcpy.AddMessage('No hay metadato')
    ruta = rasterList[1].split('.')[0].split("_")
    
    res_temporal = ruta[3]
    nivel_pr = "L2"
    ang_incidencia = "0"
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    file = rasterList[1].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'DMC'):
    arcpy.AddMessage('Imagen numero '+str(j))
    arcpy.AddMessage('Analizando la imagen '+str(file))
    env.workspace = ndir
    ext = sensores[sensor][0]
    rasterList = arcpy.ListRasters("*", ext)
    #formato = sensores[sensor][1]
    imagen = ndir + "\\" + rasterList[0]
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, rasterList[0], style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer MET
    arcpy.AddMessage('No se puede leer el metadato .Sip')
    
    res_temporal = ""
    nivel_pr = "L1R"
    ang_incidencia = "0"
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    file = rasterList[0].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  elif(sensor == 'KOMPSAT'):
    arcpy.AddMessage('Imagen numero '+str(j))
    arcpy.AddMessage('Analizando la imagen '+str(file))
    filesd = os.listdir(ndir)
    ndir_n = ndir + "\\" + filesd[0]
    filesdn = os.listdir(ndir_n)
    filesdn.sort()
    ndir_nn = ndir_n + "\\" + filesdn[0]
    env.workspace = ndir_nn
    ext = sensores[sensor][0]
    rasterList = arcpy.ListRasters("*", ext)
    #formato = sensores[sensor][1]
    imagen = ndir_nn + "\\" + rasterList[0]
    rasterObj = arcpy.Raster(imagen)
    wsrv.write(j, 0, rasterList[0], style1)
    wsrv.write(j, 11, imagen, style1)
    respectral,rradiom,respacial,srfespacial = resexcel(wsrv,rasterObj,style1,j,sensor)
    #Leer TXT
    arcpy.AddMessage("Leyendo txt..")
    txtdrv = ndir_nn + "\\" + rasterList[0].split('.')[0] + ".txt"
    f = open(txtdrv, "r")
    content = f.read()
    #Extraer punto
    rt = content.find("AUX_REQUESTER_DATETIME")
    npr = content.find("AUX_IMAGE_LEVEL")
    ai = content.find("AUX_IMAGE_SATELLITE_INCIDENCE_DEG")
    res_temporal = content[rt+len("AUX_REQUESTER_DATETIME")+1:rt+len("AUX_REQUESTER_DATETIME")+15]
    nivel_pr = content[npr+len("AUX_IMAGE_LEVEL")+1:npr+len("AUX_IMAGE_LEVEL")+4]
    ang_incidencia = content[ai+len("AUX_IMAGE_SATELLITE_INCIDENCE_DEG")+1:ai+len("AUX_IMAGE_SATELLITE_INCIDENCE_DEG")+8]
    wsrv.write(j, 7, res_temporal, style1)
    wsrv.write(j, 12, nivel_pr, style1)
    wsrv.write(j, 13, round(float(ang_incidencia),2), style1)
    file = rasterList[0].split('.')[0]
    ext = " "
    #Generar Nubes
    areanubes, banda1, image_band_1_out = masknubes(rasterObj,imagen,rutasalida,file,salidanub,ext,vfiltro)
    wsrv.write(j, 9, round(areanubes,3), style1)
    
    #Generar Footprint
    areaimagen, prcnub, salidaftp = footprinti(banda1,rutasalida,file,ext,respacial,respectral,rradiom,srfespacial,res_temporal,areanubes,imagen,nivel_pr,ang_incidencia,image_band_1_out,sensor)
    wsrv.write(j, 8, round(areaimagen,3), style1)
    wsrv.write(j, 10, round(prcnub,2), style1)
    #Cruce Dpto y Mpio
    nombredepto_str, nombremunipio_str = crdptompio(salidaftp,dtos,mpios,rutasalida,file,salidafoot)
    wsrv.write(j,1,nombredepto_str.capitalize())
    wsrv.write(j,2,nombremunipio_str.capitalize())
    arcpy.ClearWorkspaceCache_management()
    arcpy.AddMessage('\n')
    arcpy.AddMessage('\n')
  
wbrv.save(rutasalida+'\ReporteSatelital.xls')
