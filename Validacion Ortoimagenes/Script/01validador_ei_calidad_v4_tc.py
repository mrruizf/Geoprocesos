"""Este script permite evaluar el cumplimiento de las medidas de estructura e integridad de una imagen (Resolucion espacial, radiometrica, espectral y su sistema
   de referencia, tambien permite calcular el porcentaje para la calidad por omision y generar los puntos sugeridos a evaluar en la exactitud posicional, las variables 
   de ingreso corresponden a:
  --directorio: Ruta de la carpeta en donde se encuentra(n) la(s) imagen(es) a analizar
  --rutavectores: Ruta de la carpeta en donde se encuentran los archivos vectoriales a analizar y se guardaran los generados.
  --escala: Escala a la que se desea generar los productos.
  --directorioe: Ruta del archivo de excel donde se guardaran los resultados de la validacion
  --vfiltro: Valor a filtrar en la banda 1 para la extraccion de nubes
  --directorioe: Ruta del archivo de excel donde se guardaran los resultados de la validacion
  El resultado obtenido es un excel que indica si la imagen cumple o no cumple con cada una de las medidas analizadas,un excel que indica el porcentaje de perdida 
  de informacion en el area del proyecto por nubes y otros elementos, una capa de areas detectadas como nubes y los puntos sugeridos a evaluar en la 
  exactitud posicional.
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
from xlutils.copy import copy
import xlwt

# if __name__ == "__main__":
 
#  parser = argparse.ArgumentParser(description='Validador de Imagenes - IGAC')
#  parser.add_argument('--directorio', type=str, help="e.g. C:\Imagenes")
#  parser.add_argument('--rutavectores', type=str, help="e.g. C:\Vector")
#  #parser.add_argument('--nameimg', type=str, help="e.g. Imagen001")
#  #parser.add_argument('--namearea', type=str, help="e.g. Area_Pr")
#  parser.add_argument('--escala', type=int, help="e.g. 10000")
#  parser.add_argument('--directorioe', type=str, help="e.g. C:\Excel.xls")
#  parser.add_argument('--vfiltro', type=int, help="e.g. 240")

#  # In case any parameter is passed
#  args = parser.parse_args()
#  directorio = "C:\Imagenes" if not args.directorio else args.directorio
#  rutavectores = "C:\Imagenes" if not args.rutavectores else args.rutavectores
#  #nameimg = "Imagen001" if not args.nameimg else args.nameimg
#  #namearea = "Area_Pr" if not args.namearea else args.namearea
#  escala = "1000" if not args.escala else args.escala
#  directorioe = "C:\Excel.xls" if not args.directorioe else args.directorioe
#  vfiltro = 240 if not args.vfiltro else args.vfiltro
arcpy.CheckOutExtension("spatial")
"""
directorio = input("Indique la ruta donde se encuentran las imagenes: ") 
rutavectores = input("Indique la ruta donde se encuentran los archivos vectoriales: ") 
escala = int(input("Indique la escala de trabajo de las imagenes: "))
directorioe = input("Indique la ruta y nombre de la plantilla de excel a diligenciar: ")
vfiltro = int(input("Indique el valor del ND a filtrar en la banda 1 para la extraccion de nubes: "))
"""
directorio = arcpy.GetParameterAsText(0)
rutavectores = arcpy.GetParameterAsText(1)
escala = arcpy.GetParameterAsText(2)
directorioe = arcpy.GetParameterAsText(3)
vfiltro = arcpy.GetParameterAsText(4)
def SelectRandomByCount(layer, count, salidapuntos):
    layerCount = int(arcpy.GetCount_management(layer).getOutput(0))
    if layerCount < count:
        print "NO EXISTEN SUFICIENTES PUNTOS PARA SELECIONAR"
        return
    oids = [oid for oid, in arcpy.da.SearchCursor(layer, "OID@")]
    oidFldName = arcpy.Describe(layer).OIDFieldName
    delimOidFld = arcpy.AddFieldDelimiters(layer, oidFldName)
    randOids = random.sample(oids, count)
    oidsStr = ",".join(map(str, randOids))
    sql = "{0} IN ({1})".format(delimOidFld, oidsStr)
    arcpy.MakeFeatureLayer_management (layer, "stateslyrs")
    arcpy.SelectLayerByAttribute_management("stateslyrs", "", sql)
    arcpy.CopyFeatures_management("stateslyrs", salidapuntos)
    arcpy.Delete_management("stateslyrs")

codeblock = """rec=0
def autoIncrement():
  global rec
  pStart = 1
  pInterval = 1
  if (rec == 0):
    rec = pStart
  else:
    rec += pInterval
  return rec"""

formatos = {'tif' : 'TIFF', 'img' : 'IMG', 'ecw': 'ECW', 'sid': 'MrSID', 'jp2': 'JPEG2000'}
areas = {"1000":50, "2000":100, "5000":250, "10000":500, "25000":1000,"50000":2500}
areasf = {"1000":1, "2000":4, "5000":25, "10000":100, "25000":615,"50000":2500}
ccarto = {"1000":'0', "2000":('0','1'), "5000":('0','1','2'), "10000":('0','1','2','3'), "25000":('0','1','2','3','4'),"50000":('0','1','2','3','4','5'),"100000":('0','1','2','3','4','5','6'),"150000":('0','1','2','3','4','5','6','7'),"200000":('0','1','2','3','4','5','6','7','8'),"300000":('0','1','2','3','4','5','6','7','8','9'),"350000":('0','1','2','3','4','5','6','7','8','9','10'),"400000":('0','1','2','3','4','5','6','7','8','9','10','11'),"500000":('0','1','2','3','4','5','6','7','8','9','10','11','12'),"750000":('0','1','2','3','4','5','6','7','8','9','10','11','12','13')}

nowd = datetime.now()
os.chdir(directorio)
env.workspace = directorio
rasterList = arcpy.ListRasters()
rb = open_workbook(directorioe, formatting_info=True)
wb = copy(rb)
ws = wb.get_sheet(1)
ws.write(13,2,str(nowd.year))
ws.write(13,4,str(nowd.month))
ws.write(13,6,str(nowd.day))
ws.write(11,31,str(1))
ws.write(8,34,str(escala))

#Crear excel resumen
style0 = xlwt.easyxf('font: name Abadi, colour black, bold on, height 220')
wbrv = xlwt.Workbook()
wsrv = wbrv.add_sheet('Resumen_Validadores',cell_overwrite_ok=True)
#wsrv.write(0, 0, 'Estructura e Integridad', style0)
wsrv.write(0, 0, 'Caracteristica', style0)
wsrv.write(0, 1, 'Valor_Observado', style0)
wsrv.write(1, 0, 'Resolucion espacial', style0)
wsrv.write(2, 0, 'Resolucion espectral', style0)
wsrv.write(3, 0, 'Resolucion radiometrica', style0)
wsrv.write(4, 0, 'Sistema de Referencia', style0)
wsrv.write(5, 0, 'Area Proyecto (Ha)', style0)
wsrv.write(6, 0, 'Area Omision (%)', style0)
wsrv.write(7, 0, 'Exactitud Posicional', style0)
wsrv.write(8, 0, 'Empalme', style0)
wsrv.write(9, 0, 'Distorsion geometrica', style0)
wsrv.write(10, 0, 'Desbalanceo radiometrico', style0)
wsrv.write(11, 0, 'Formato de entrega y despliegue', style0)

#Configurar esta ruta segun donde se ubique el script
"""
ptocontrol = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\Puntos_Control\Pto_Control.shp'
redpasiva = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\Red_Pasiva_15112019\Red_Pasiva_15112019.shp'
dtos = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\Departamentos\Dptos.shp'
mpios = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\Municipios\Mpios.shp'
cubcarto = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\Cubrimiento_Cartografia.gdb\Cubrimiento_Cartografia'
ptofotog = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\PROCESO_FOTOGRAMETRICO.gdb\AEROTRIANGULACION\PUNTO_FOTOGRAMETRICO'
gdbincons = r'C:\Users\Jonnyy\Documents\Jonnyy\Work\IGAC\2021\00_CARTO_BASE\GDB_INCONSISTENCIAS\Inconsistencias_Orto.gdb'
"""
ptocontrol = arcpy.GetParameterAsText(5)
redpasiva = arcpy.GetParameterAsText(6)
dtos = arcpy.GetParameterAsText(7)
mpios = arcpy.GetParameterAsText(8)
cubcarto = arcpy.GetParameterAsText(9)
ptofotog = arcpy.GetParameterAsText(10)
gdbincons = arcpy.GetParameterAsText(11)
for raster in rasterList:
  #Leer Imagen
  ruta = directorio+"\\"+ raster #+ ".tif"
  ws.write(15,8,str(ruta))
  rasterObj = arcpy.Raster(ruta)
  print('Analizando la imagen ', raster)
  #Obtener medidas
  respectral = rasterObj.bandCount
  rradiom = rasterObj.pixelType
  respacial = rasterObj.meanCellWidth
  srfespacial = rasterObj.spatialReference.name
  #Escribir al excel
  ws.write(11,30,str(round(respacial,2))+' m')
  ws.write(12,30,str(respectral))
  wsrv.write(1, 1, str(round(respacial,2)), style0)
  wsrv.write(2, 1, str(respectral), style0)
  
  
  #Verificar Resolucion Espectral (Numero de bandas)
  if respectral >= 3:
    print 'La imagen: ' + raster + ' posee ' + str(respectral) + ' bandas, por lo tanto SI cumple con la resolucion espectral'
    #ws.write(3,2,'SI')
  else:
    print 'La imagen: ' + raster + ' posee ' + str(respectral) + ' bandas, por lo tanto NO cumple con la resolucion espectral'
    #ws.write(3,2,'NO')
  
  # #Verificar Resolucion Radiometrica (Numero de bits)
  tam = len(rradiom)
  if tam >= 3:
    print 'La imagen: ' + raster + ' posee una resolucion radiometrica de ' + rradiom + ' bits, por lo tanto SI cumple con la resolucion radiometrica'
    #ws.write(4,2,'SI')
    ws.write(13,30,str(rradiom[1:]))
    wsrv.write(3, 1, str(rradiom[1:]), style0)
  else:
    num = rradiom[1]
    if num >= 8:
      print 'La imagen: ' + raster + ' posee una resolucion radiometrica de ' + rradiom + ' bits, por lo tanto SI cumple con la resolucion radiometrica'
      #ws.write(4,2,'SI')
    else:
      print 'La imagen: ' + raster + ' posee ' + respectral + ' bits, por lo tanto NO cumple con la resolucion espectral'
      #ws.write(4,2,'NO')
    ws.write(13,30,str(num))
    wsrv.write(3, 1, str(num), style0)

  # #Verificar Resolucion Espacial (Segun la escala)
  escalav = escala/100
  respcm = respacial*100
  if respcm <= escalav:
    print 'La imagen: ' + raster + ' posee un GSD de ' + str(respcm) + ' cm, por lo tanto SI cumple con la resolucion espacial para la escala indicada de: ' + str(escala)
    #ws.write(2,2,'SI')
  else:
    print 'La imagen: ' + raster + ' posee un GSD de ' + str(respcm) + ' cm, por lo tanto NO cumple con la resolucion espacial para la escala indicada de: ' + str(escala)
    #ws.write(2,2,'NO')

  ##Verificar Sistema de referencia
  if srfespacial == "MAGNA_CTM12" or srfespacial == "MAGNA-SIRGAS / Origen-Nacional" or srfespacial == "MAGNA_SIRGAS_Origen_Nacional":
    print 'La imagen: ' + raster + ' posee el sistema de referencia ' + srfespacial+ ', por lo tanto SI cumple con el sistema de referencia.'
    #ws.write(5,2,'SI')
    ws.write(13,32,"MAGNA SIRGAS")
    ws.write(13,34,"Nacional")
    ws.write(24,28,"Origen Nacional")
    ws.write(24,30,"CONFORME")
    wsrv.write(4, 1, "MAGNA SIRGAS-Origen Nacional", style0)
  else:
    print 'La imagen: ' + raster + ' posee el sistema de referencia ' + srfespacial+ ', por lo tanto NO cumple con el sistema de referencia.'
    #ws.write(5,2,'NO')
    ws.write(13,32,srfespacial)
    ws.write(13,34,srfespacial)
    ws.write(24,28,srfespacial)
    ws.write(24,30,"NO CONFORME")
    ws.write(24,32,"No cumple")
    wsrv.write(4, 1, srfespacial, style0)


  print("\n")
  nmraster = raster.split(".")
  namearea = nmraster[0]
  frm = nmraster[1]
  if frm in formatos.keys():
    formator = formatos[nmraster[1]]
    ws.write(13,20,formator)
    ws.write(23,28,'VERDADERO')
    ws.write(23,30,'CONFORME')
    wsrv.write(11, 1, formator, style0)
  else:
    ws.write(13,20,frm)
    ws.write(23,28,'FALSO')
    ws.write(23,30,'NO CONFORME')
    wsrv.write(11, 1, frm, style0)
  
  ws.write(4,32,namearea)
  #namearea = namearea.replace('-','')
  #namearea = namearea.replace('.','')

  #Leer Imagen
  desc = arcpy.Describe(rasterObj)
  nband1 = desc.children[0].name
  band1 = ruta+"\\"+nband1
  print('Generando Banda 1 para su filtrado')
  image_band_1_out = os.path.join(directorio, namearea +'_band_1.tif')
  arcpy.CopyRaster_management(band1,image_band_1_out)
  banda1 = arcpy.Raster(image_band_1_out)
  #Filtrar imagen en la Banda 1
  rradiom = rasterObj.pixelType
  print 'La radiometria de la imagen es: ' + rradiom
  tam = len(rradiom)
  if tam >= 3:
    filtim = banda1 > vfiltro
  else:
    filtim = banda1 > vfiltro

  rutasalida = rutavectores + "\\" + namearea
  #print(rutasalida)
  os.mkdir(rutasalida)
  print('Filtrando nubes para su cuantificacion')
  attExtract = ExtractByAttributes(filtim, "VALUE =1")
  salidanub = rutasalida+"\polnubes"+namearea.replace('-','')+".shp"
  #Conversion a Poligono
  arcpy.RasterToPolygon_conversion(attExtract, salidanub , "NO_SIMPLIFY","VALUE")
  arcpy.MakeFeatureLayer_management(salidanub, "nub"+namearea)
  areapr = rutavectores + "\\" + namearea + ".shp"
  salidacl = rutasalida + "\\ANubes"+namearea.replace('-','')+".shp"
  #Cortar area de nubosidad al area del proyecto
  arcpy.Clip_analysis("nub"+namearea, areapr, salidacl)
  print('Calculando areas de nubosidad')
  arcpy.AddField_management(salidacl, "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
  srfespacial = rasterObj.spatialReference.name
  print 'El sistema de referencia de la imagen es: ' + srfespacial
  exp = "!SHAPE.AREA@SQUAREMETERS!"
  arcpy.CalculateField_management(salidacl, "Area_ha", exp, "PYTHON_9.3")
  arcpy.MakeFeatureLayer_management(salidacl, "anubesf")
  expf = "Area_ha > " + str(areasf[str(escala)])
  arcpy.SelectLayerByAttribute_management("anubesf", "NEW_SELECTION", expf)
  salidaclf = rutasalida + "\\ANubesF"+namearea.replace('-','')+".shp"
  arcpy.CopyFeatures_management("anubesf", salidaclf)
  salidatb = rutasalida + "\\tabla" + namearea
  #Sumar areas de registros
  arcpy.Statistics_analysis(salidaclf, salidatb, [["Area_ha", "SUM"]])
  field_names = [i.name for i in arcpy.ListFields(salidatb) if i.type != 'OID']
  cursor = arcpy.da.SearchCursor(salidatb, field_names)
  data=[row for row in cursor]
  if data == []:
    print('No se generaron registros filtrados en areas de nubosidad')
    areaomitida = 0
  else:
    areaomitida = (data[0][2])/10000
  print 'El area omitida por nubosidad corresponde a ' + str(round(areaomitida,2)) + ' Ha'
  arcpy.Delete_management("anubesf")
  arcpy.Delete_management(salidacl)
  #ws.write(6,1,str(round(areaomitida,2)))


  print('Calculando otras areas omitidas')
  filtim2 = banda1 > 0
  attExtract2 = ExtractByAttributes(filtim2, "VALUE =1")
  salidaftp = rutasalida+"\\footp"+namearea.replace('-','')+".shp"
  arcpy.RasterToPolygon_conversion(attExtract2, salidaftp , "NO_SIMPLIFY","VALUE")
  eraseOutput = rutasalida+"\\aom"+namearea.replace('-','')+".shp"
  arcpy.Erase_analysis(areapr, salidaftp, eraseOutput)
  arcpy.AddField_management(eraseOutput, "Area_ha2", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management(eraseOutput, "Area_ha2", exp, "PYTHON_9.3")
  salidatb3 = rutasalida + "\\tabla3" + namearea
  #Sumar areas de registros
  arcpy.Statistics_analysis(eraseOutput, salidatb3, [["Area_ha2", "SUM"]])
  field_names3 = [i.name for i in arcpy.ListFields(salidatb3) if i.type != 'OID']
  cursor3 = arcpy.da.SearchCursor(salidatb3, field_names3)
  dataom=[row for row in cursor3]
  if dataom == []:
    print('No se generaron registros filtrados en otras areas omitidas')
    areaomitida2 = 0
  else:
    areaomitida2 = dataom[0][2]
  print 'El area omitida otras zonas corresponde a ' + str(round(areaomitida2,2)) + ' Ha'
  #ws.write(7,1,str(round(areaomitida2,2)))


  print('Calculando area del proyecto')
  arcpy.AddField_management(areapr, "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management(areapr, "Area_ha", exp, "PYTHON_9.3")
  salidatb2 = rutasalida + "\\tabla2" + namearea
  #Sumar areas del area del proyecto
  arcpy.Statistics_analysis(areapr, salidatb2, [["Area_ha", "SUM"]])
  field_namespr = [i.name for i in arcpy.ListFields(areapr) if i.type != 'OID']
  cursorpr = arcpy.da.SearchCursor(areapr, field_namespr)
  datapr =[row for row in cursorpr]
  colum = len(field_namespr) - 1
  areaproyecto = datapr[0][colum]
  print 'El area del proyecto es ' + str(round(areaproyecto,2)) + ' Ha'
  #ws.write(8,1,str(round(areaproyecto,2)))
  ws.write(11,20,str(round(areaproyecto,2)))
  wsrv.write(5, 1, str(round(areaproyecto,2)), style0)

  promision = ((areaomitida+areaomitida2)/areaproyecto)*100
  prfomision = round(promision,2)
  #ws.write(9,1,str(prfomision))
  ws.write(18,28,str(prfomision))
  promision1 = (areaomitida/areaproyecto)*100
  promision2 = (areaomitida2/areaproyecto)*100
  ws.write(18,32,"Area omitida por nubosidad: "+str(round(areaomitida,2))+" ("+str(round(promision1,2))+ "%) "+", Area omitida por otras areas: "+ str(round(areaomitida2,2))+" (" + str(round(promision2,2))+ "%) ")
  if prfomision < 3:
    print 'El area total de omision corresponde a ' + str(prfomision) + '%, por lo tanto SI cumple con la Calidad de Omision'
    ws.write(18,30,"CONFORME")
  else:
    print 'El area total de omision corresponde a ' + str(prfomision) + '%, por lo tanto NO cumple con la Calidad de Omision'
    ws.write(18,30,"NO CONFORME")
    #ws.write(9,2,'NO')
  wsrv.write(6, 1, str(prfomision), style0)

  #Interseccion AreaPr y footprint imagen
  inFeaturesi = [salidaftp, areapr]
  outName_int = rutasalida + "\\" + 'AreaT_'+namearea.replace('-','')+'.shp'
  outName_intp = rutasalida + "\\" + 'AreaTPr_'+namearea.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeaturesi, outName_int)
  sptref = arcpy.Describe(areapr).spatialreference
  arcpy.Project_management(outName_int, outName_intp, sptref)

  #Cruce Dtos y Mpios
  arcpy.MakeFeatureLayer_management (dtos, "departamento")
  inFeatures_pcd = ["departamento", outName_intp]
  outName_pcd = rutasalida + "\\" + 'Areadpto_'+namearea.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_pcd, outName_pcd)
  arcpy.MakeFeatureLayer_management (outName_pcd, "areadpto")
  arcpy.AddField_management("areadpto", "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management("areadpto", "Area_ha", exp, "PYTHON_9.3")
  out_sort =  rutasalida + "\\" + 'Areadptoso_'+namearea.replace('-','')+'.shp'
  arcpy.Sort_management("areadpto", out_sort, [["Area_ha", "DESCENDING"]])
  arcpy.MakeFeatureLayer_management (out_sort, "areadptos")
  #arcpy.SelectLayerByLocation_management("departamento", "intersect", outName_intp)
  cursor = arcpy.da.SearchCursor('areadptos', ['Departamen','Area_ha'])
  nombredepto = []
  for row in cursor:
    nombredepto.append(("{0}".format(row[0].encode('UTF-8'))))
  nombredepto_str = ''
  for n in nombredepto:
    nombredepto_str += str(n) + ", "
  nombredepto_str = nombredepto_str[:-2].decode('UTF-8')
  ws.write(9,8,nombredepto_str.capitalize())
  arcpy.Delete_management("departamento")
  arcpy.Delete_management("areadpto")
  arcpy.Delete_management("areadptos")
  arcpy.Delete_management(outName_pcd)
  arcpy.Delete_management(out_sort)

  arcpy.MakeFeatureLayer_management (mpios, "municipios")
  inFeatures_pcm = ["municipios", outName_intp]
  outName_pcm = rutasalida + "\\" + 'Areampio_'+namearea.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_pcm, outName_pcm)
  arcpy.MakeFeatureLayer_management (outName_pcm, "areampio")
  arcpy.AddField_management("areampio", "Area_ha", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
  exp = "!SHAPE.AREA@HECTARES!"
  arcpy.CalculateField_management("areampio", "Area_ha", exp, "PYTHON_9.3")
  out_sort =  rutasalida + "\\" + 'Areampios_'+namearea.replace('-','')+'.shp'
  arcpy.Sort_management("areampio", out_sort, [["Area_ha", "DESCENDING"]])
  arcpy.MakeFeatureLayer_management (out_sort, "areampios")
  #arcpy.SelectLayerByLocation_management("municipios", "intersect", outName_intp)
  cursormunicipio = arcpy.da.SearchCursor('areampios', ['NOM_MUNICI','Area_ha'])
  nombremunipio = []
  for row in cursormunicipio:
    nombremunipio.append(("{0}".format(row[0].encode('UTF-8'))))
  nombremunipio_str = ''
  for n in nombremunipio:
    nombremunipio_str += str(n) + ", "
  nombremunipio_str = nombremunipio_str[:-2].decode('UTF-8')
  ws.write(9,26,nombremunipio_str.capitalize())
  arcpy.Delete_management("municipios")
  arcpy.Delete_management("areampio")
  arcpy.Delete_management("areampios")
  arcpy.Delete_management(outName_pcm)
  arcpy.Delete_management(out_sort)

  print '\n'
  #Guardar Excel
  print('Guardando Excel')
  ruta = directorioe.split("\\")
  rnew = ruta[:-1]
  sep = "\\"
  rutanueva = sep.join(rnew)
  wb.save(rutasalida+'\ReporteValidacion_'+namearea+'.xls')
  wbrv.save(rutasalida+'\\ResumenValidacion_'+namearea+'.xls')

  # Generar los puntos aleatorios
  print 'Generacion de puntos para la exactitud posicional'
  outName_pc = rutasalida + "\\" + 'Puntosfc_'+namearea.replace('-','')+'.shp'
  inFeatures_pc = [ptocontrol, outName_intp]
  arcpy.Intersect_analysis(inFeatures_pc, outName_pc)
  inFeatures_rp = [redpasiva, outName_intp]
  outName_rp = rutasalida + "\\" + 'Puntosrp_'+namearea.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_rp, outName_rp)
  inFeatures_pf = [ptofotog, outName_intp]
  outName_pf = rutasalida + "\\" + 'Puntosfot_'+namearea.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_pf, outName_pf)

  #arcpy.Append_management(outName_rp, outName_pc, "NO_TEST","","")
  #arcpy.Delete_management(outName_rp)
  #out_points = rutasalida + "\\" + 'Puntos_Ep'+namearea.replace('-','')+'.shp'
  #SelectRandomByCount(outName_pc,20,out_points)
  #arcpy.Delete_management(outName_pc)
  #arcpy.CreateRandomPoints_management(rutasalida, outName, salidaftp, "", 20, minDistance)
  print 'Puntos YA generados para la exactitud posicional'
  print("\n")
  print 'Generacion de capa Cartografia Existente'
  #Cruce Cubrimiento Cartografia
  arcpy.MakeFeatureLayer_management(cubcarto, "ccartog")
  expfc = "ESCALA IN " + str(ccarto[str(escala)])
  arcpy.SelectLayerByAttribute_management("ccartog", "NEW_SELECTION", expfc)
  salidaclfc = rutasalida + "\\CC"+namearea.replace('-','')+".shp"
  arcpy.CopyFeatures_management("ccartog", salidaclfc)
  inFeatures_cc = [salidaclfc, outName_intp]
  outName_cc = rutasalida + "\\" + 'CCarto_'+namearea.replace('-','')+'.shp'
  arcpy.Intersect_analysis(inFeatures_cc, outName_cc)
  arcpy.Delete_management(salidaclfc)
  arcpy.Delete_management("ccartog")

  #Generar grilla y marcos de control
  print("Generando grilla...")
  valesc = areas[str(escala)]
  extent = arcpy.Describe(outName_intp).extent
  arcpy.env.outputCoordinateSystem = sptref
  coords = str(extent.XMin) + " " + str(extent.YMin)
  yAxisCoordinate = str(extent.XMin) + " " + str(extent.YMin+1)
  oppositeCoorner = str(extent.XMax) + " " + str(extent.YMax)
  outpg = rutasalida + "\\" + 'MarcosC_'+namearea.replace('-','')+'.shp'
  arcpy.CreateFishnet_management (outpg, coords, yAxisCoordinate, valesc, valesc, "0", "0", oppositeCoorner, "NO_LABELS", "", "POLYGON")

  result= arcpy.GetCount_management(outpg)
  count = int(result.getOutput(0))
  z = 1.64
  p = 0.5
  e = 0.1
  a = (z*z)*(p)*(1-p)
  b = (e*e)
  c = (count-1)/ float(count)
  d = count*(e*e)
  ef = a/d
  f = c + ef
  g = a/b
  o = g/f 
  h = int(o)

  #Interseccion Grilla con area proyecto que coincide con la imagen
  salidagrillai = rutasalida + "\\" + 'MarcosCI_'+namearea.replace('-','')+'.shp'
  arcpy.MakeFeatureLayer_management (outpg, "grillat")
  arcpy.SelectLayerByLocation_management("grillat", "intersect", outName_intp)
  arcpy.CopyFeatures_management("grillat", salidagrillai)
  #arcpy.AddField_management(salidagrillai, "Id", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
  expression = "autoIncrement()"
  arcpy.CalculateField_management(salidagrillai, "Id", expression, "PYTHON_9.3", codeblock)

  
  outName = 'PuntosA.shp'
  arcpy.CreateRandomPoints_management(rutasalida, outName, outName_intp, "", h, valesc)
  print("Generando Marcos de control..")
  arcpy.MakeFeatureLayer_management (salidagrillai, "grillati")
  arcpy.SelectLayerByLocation_management("grillati", "intersect", rutasalida+"\\"+outName)
  salidagrillap = rutasalida + "\\" + 'MarcosCS_'+namearea.replace('-','')+'.shp'
  arcpy.CopyFeatures_management("grillati", salidagrillap)
  print("Marcos de control generados")

  arcpy.Delete_management(rutasalida+"\\"+outName)
  arcpy.Delete_management(outName_int)
  #arcpy.Delete_management(outName_intp)
  arcpy.Delete_management("grillat")
  arcpy.Delete_management("grillati")
  arcpy.Delete_management(outpg)

  #Generando Shapefile
  salidainc = rutasalida+'\\Inconsistencias_'+namearea.replace('-','')+'.gdb'
  arcpy.Copy_management(gdbincons, salidainc)
  # arcpy.CreateFeatureclass_management(rutasalida, 'Inconsistencias_'+namearea.replace('-','')+'.shp', "POLYGON","","","",sptref)
  # arcpy.AddField_management(salidainc, "AREA", "DOUBLE", "", "", "", "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "PERIMETER", "DOUBLE", "", "", "", "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "PRIORIDAD", "TEXT", "", "", 1, "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "ESTADO", "TEXT", "", "", 50, "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "OBS", "TEXT", "", "", 200, "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "ERROR", "TEXT", "", "", 3, "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "Respuesta", "TEXT", "", "", 200, "", "NULLABLE", "REQUIRED")
  # arcpy.AddField_management(salidainc, "OBS_1", "TEXT", "", "", 50, "", "NULLABLE", "REQUIRED")

  #Borrar archivos temporales
  #arcpy.Delete_management(salidacl)
  arcpy.Delete_management(salidaftp)
  #arcpy.Delete_management(eraseOutput)
  arcpy.Delete_management(salidanub)
  arcpy.Delete_management(image_band_1_out)
  arcpy.Delete_management(salidatb3)
  arcpy.Delete_management(salidatb2)
  arcpy.Delete_management(salidatb)
  arcpy.ClearWorkspaceCache_management()
