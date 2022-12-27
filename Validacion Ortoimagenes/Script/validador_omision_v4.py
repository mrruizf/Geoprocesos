"""Este script permite calcular el porcentaje para la calidad por omision, las variables de ingreso corresponden a:
  --rutavectores: Ruta de la carpeta en donde se encuentran los archivos vectoriales y donde se guardaran los generados
  --txtdrv: Ruta txt con medida rmse.
  --txtdrv: tipo de muestreo para las medidas de inconsistencias.
  El resultado obtenido corresponde al porcentaje de perdida de informacion en el area del proyecto por nubes y otros elementos.
  Autor: Maycol Zaraza
   """
import arcpy
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

if __name__ == "__main__":
 arcpy.CheckOutExtension("spatial")
 parser = argparse.ArgumentParser(description='Validador de Imagenes - IGAC')
 parser.add_argument('--rutavectores', type=str, help="e.g. C:\Vector")
 #parser.add_argument('--namecloud', type=str, help="e.g. AreasNubes")
 #parser.add_argument('--areaomitidaoz', type=float, help="e.g. 50.23")
 #parser.add_argument('--directorioe', type=str, help="e.g. Excel.xls")
 #parser.add_argument('--escala', type=int, help="e.g. 10000")
 parser.add_argument('--txtdrv', type=str, help="e.g. C:\TxtDRV.txt")
 parser.add_argument('--tmuestreo', type=int, help="e.g. 1")
 #parser.add_argument('--rutainct', type=str, help="e.g. C:\Inconsistencias.shp")

 # In case any parameter is passed
 args = parser.parse_args()
 rutavectores = "C:\Vector" if not args.rutavectores else args.rutavectores
 #namecloud = "AreasNubes" if not args.namecloud else args.namecloud
 #areaomitidaoz = 1 if not args.areaomitidaoz else args.areaomitidaoz
 #directorioe = "C:\Excel.xls" if not args.directorioe else args.directorioe
 #escala = "1000" if not args.escala else args.escala
 txtdrv = "" if not args.txtdrv else args.txtdrv
 tmuestreo = 1 if not args.tmuestreo else args.tmuestreo
 #rutainct = "Inconsistencias" if not args.rutainct else args.rutainct


nameimagen = rutavectores.split("\\")[-1]
namecloud = "ANubesF"+ nameimagen.replace('-','')
shpomitidaoz = rutavectores+ "\\" + "aom"+ nameimagen.replace('-','') + ".shp"
directorioe = "ReporteValidacion_"+nameimagen
rutainct = "Inconsistencias_"+nameimagen.replace('-','') + ".gdb"
excelrv = "ResumenValidacion_"+nameimagen

plexcel =  rutavectores + "\\" + directorioe + ".xls"
rb = open_workbook(plexcel, formatting_info=True)
wb = copy(rb)
ws = wb.get_sheet(1)
nowd = datetime.now()
ws.write(13,8,str(nowd.year))
ws.write(13,10,str(nowd.month))
ws.write(13,12,str(nowd.day))

#Excel Resumen Validadores
rvexcel =  rutavectores + "\\" + excelrv + ".xls"
rve = open_workbook(rvexcel, formatting_info=True)
wbrv = copy(rve)
wsrv = wbrv.get_sheet(0)
style0 = xlwt.easyxf('font: name Abadi, colour black, bold on, height 220')

env.workspace = rutavectores
umbral = {"1000":0.3, "2000":0.6, "5000":1.5, "10000":3, "25000": 7.5}
#rasterList = arcpy.ListRasters()
#rasterList = os.listdir(directorio)

areanub = rutavectores + "\\"+ namecloud +".shp"
#Cortar area de nubosidad al area del proyecto
print('Calculando areas de nubosidad')
arcpy.AddField_management(areanub, "Area_ha2", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
exp = "!SHAPE.AREA@HECTARES!"
arcpy.CalculateField_management(areanub, "Area_ha2", exp, "PYTHON_9.3")
salidatb = rutavectores + "\\t" + namecloud
#Sumar areas de registros
arcpy.Statistics_analysis(areanub, salidatb, [["Area_ha2", "SUM"]])
field_names = [i.name for i in arcpy.ListFields(salidatb) if i.type != 'OID']
cursor = arcpy.da.SearchCursor(salidatb, field_names)
data=[row for row in cursor]
colum = len(field_names) - 1
if data == []:
	areaomitida = 0
else:
    areaomitida = data[0][colum]
print 'El area omitida por nubosidad corresponde a ' + str(round(areaomitida,2)) + ' Ha'
arcpy.Delete_management(salidatb)

#Extraer areas omitida otras zonas
exp = "!SHAPE.AREA@HECTARES!"
arcpy.CalculateField_management(shpomitidaoz, "Area_ha2", exp, "PYTHON_9.3")
salidatb1 = rutavectores + "\\ta" + nameimagen.replace('-','')
#Sumar areas de registros
arcpy.Statistics_analysis(shpomitidaoz, salidatb1, [["Area_ha2", "SUM"]])
field_names = [i.name for i in arcpy.ListFields(salidatb1) if i.type != 'OID']
cursor = arcpy.da.SearchCursor(salidatb1, field_names)
data=[row for row in cursor]
colum = len(field_names) - 1
if data == []:
	areaomitidaoz = 0
else:
    areaomitidaoz = data[0][colum]
print 'El area omitida por otras zonas corresponde a ' + str(round(areaomitidaoz,2)) + ' Ha'
arcpy.Delete_management(salidatb1)

print('Obteniendo area proyecto')
pag = rb.sheet_by_index(1)
areapr = pag.cell_value(11,20)
val = areapr.split(" ")
areaproyecto = float(val[0])
print 'El area del proyecto es ' + str(round(areaproyecto,2)) + ' Ha'

#Resolucion espacial
resp = pag.cell_value(11,30)
valrs = resp.split(" ")
respacial = float(valrs[0])

#Escala
escala = pag.cell_value(8,34)
escala = int(escala)


promision = ((areaomitida+areaomitidaoz)/areaproyecto)*100
prfomision = round(promision,2)
#ws.write(9,1,str(prfomision))
ws.write(18,28,str(prfomision))
promision1 = (areaomitida/areaproyecto)*100
promision2 = (areaomitidaoz/areaproyecto)*100
ws.write(18,32,"Area omitida por nubosidad: "+str(round(areaomitida,2))+" ("+str(round(promision1,2))+ "%) "+", Area omitida por otras areas: "+ str(round(areaomitidaoz,2))+" (" + str(round(promision2,2))+ "%) ")

if prfomision < 3:
	print 'El area total de omision corresponde a ' + str(prfomision) + '%, por lo tanto SI cumple con la Calidad de Omision'
	ws.write(18,30,"CONFORME")
else:
	print 'El area total de omision corresponde a ' + str(prfomision) + '%, por lo tanto NO cumple con la Calidad de Omision'
	ws.write(18,30,"NO CONFORME")

wsrv.write(6, 1, str(prfomision), style0)
umbrale = umbral[str(escala)]
ws.write(19,26,str(umbrale))

inconsistenciasv = rutavectores + "\\"+ rutainct +"\Inconsistencia\Inconsistencias_Orto"
print("Leyendo txt..")

if txtdrv == "":
	print("No se cargo ningun archivo txt para la extracion del RMMSE, se omitira dicha validacion")

	#Medida LC Empalme
	sql = "Tipo_Error = 2"
	arcpy.MakeFeatureLayer_management(inconsistenciasv, "incs")
	arcpy.SelectLayerByAttribute_management("incs", "NEW_SELECTION", sql)
	salida2 = rutavectores + "\\tablainc2"
	exp = "!SHAPE.AREA@HECTARES!"
	arcpy.CalculateField_management("incs", "Area", exp, "PYTHON_9.3")
	#Sumar areas de registros
	arcpy.Statistics_analysis("incs", salida2, [["Area", "SUM"]])
	cursor = arcpy.da.SearchCursor(salida2, ["SUM_AREA"])
	data=[row for row in cursor]
	if data == []:
		print('El numero de pixeles de Empalme es 0')
		npixel = 0
	else:
		emp = data[0][0]
		empm = float(emp)*10000
		npixel = empm/(respacial*respacial)
		print('El numero de pixeles por empalme es ',npixel)
	ws.write(20,28,str(int(npixel)))
	if npixel > 2:
		ws.write(20,32,'No cumple')
		ws.write(20,30,"NO CONFORME")
	else:
		ws.write(20,32,'Cumple')
		ws.write(20,30,"CONFORME")
	wsrv.write(8, 1, str(npixel), style0)

	arcpy.Delete_management("incs")

	if tmuestreo==1:
		#Calculo medidas de consistencia
		inconsistenciasv = rutavectores + "\\"+ rutainct +"\Inconsistencia\Inconsistencias_Orto"
		arcpy.MakeFeatureLayer_management(inconsistenciasv, "incs")
		#Medida DTM Distorsion Geometrica
		sql = "Tipo_Error = 1 OR Tipo_Error = 4 OR Tipo_Error = 5"
		arcpy.SelectLayerByAttribute_management("incs", "NEW_SELECTION", sql)
		salida1 = rutavectores + "\\tablainc1"
		exp = "!SHAPE.AREA@HECTARES!"
		arcpy.CalculateField_management("incs", "Area", exp, "PYTHON_9.3")
		#Sumar areas de registros
		arcpy.Statistics_analysis("incs", salida1, [["Area", "SUM"]])
		field_names = [i.name for i in arcpy.ListFields(salida1) if i.type != 'OID']
		cursor = arcpy.da.SearchCursor(salida1, ["SUM_AREA"])
		data=[row for row in cursor]
		if data == []:
			print('El area de Distorsion Geometrica es 0')
			dg = 0
		else:
			dg = data[0][0]	
		prcdg = (dg/areaproyecto)*100
		print('El area de Distorsion Geometrica es ',dg, ' corresponde a ',str(round(prcdg,2)), '%')
		ws.write(21,28,str(round(prcdg,2)))
		wsrv.write(9, 1, str(round(prcdg,2)), style0)
		if(prcdg<=1):
			ws.write(21,30,"CONFORME")
		else:
			ws.write(21,30,"NO CONFORME")

		#Medida RAD Desbalance Radiometrico
		sql = "Tipo_Error = 3"
		arcpy.SelectLayerByAttribute_management("incs", "NEW_SELECTION", sql)
		salida3 = rutavectores + "\\tablainc3"
		exp = "!SHAPE.AREA@HECTARES!"
		arcpy.CalculateField_management("incs", "Area", exp, "PYTHON_9.3")
		#Sumar areas de registros
		arcpy.Statistics_analysis("incs", salida3, [["Area", "SUM"]])
		cursor = arcpy.da.SearchCursor(salida3, ["SUM_AREA"])
		data=[row for row in cursor]
		if data == []:
			print('El area de Desbalance Radiometrico es 0')
			dr = 0
		else:
			dr = data[0][0]
		prcdr = (dr/areaproyecto)*100
		print('El area de Desbalance Radiometrico es ',dr, ' corresponde a ',str(round(prcdr,2)), '%')
		ws.write(22,28,str(round(prcdr,2)))
		wsrv.write(10, 1, str(round(prcdr,2)), style0)
		if(prcdr<=1):
			ws.write(22,30,"CONFORME")
		else:
			ws.write(22,30,"NO CONFORME")

		arcpy.Delete_management(salida1)
		arcpy.Delete_management(salida3)
	else:
		ngrilla = "MarcosCS_"+ nameimagen.replace('-','')
		grilla = rutavectores + "\\"+ ngrilla +".shp"
		ws.write(21,32,'Medida calculada con grilla')
		ws.write(22,32,'Medida calculada con grilla')
		wsrv.write(9, 1, 'Medida calculada con grilla', style0)
		wsrv.write(10, 1, 'Medida calculada con grilla', style0)
		ws.write(21,30,"")
		ws.write(22,30,"")
		inconsistenciasv = rutavectores + "\\"+ rutainct +"\Inconsistencia\Inconsistencias_Orto"
		arcpy.MakeFeatureLayer_management(inconsistenciasv, "incs")
		field_names = [i.name for i in arcpy.ListFields(grilla) if i.type != 'OID']
		cursor = arcpy.da.SearchCursor(grilla, field_names)
		wbg = xlwt.Workbook() # create empty workbook object
		newsheet = wbg.add_sheet('Grillas')
		newsheet.write(0,0,'Id_Grilla')
		newsheet.write(0,1,'Distorsion_geometrica')
		newsheet.write(0,2,'Desbalance_radiometrico')
		k=1
		for row in cursor:
		    idc = row[1]
		    exp = "Id="+str(idc)
		    print('Calculando Grilla Id: ',idc)
		    newsheet.write(k,0,idc)
		    arcpy.MakeFeatureLayer_management(grilla, "grillac")
		    arcpy.SelectLayerByAttribute_management("grillac","NEW_SELECTION",exp)
		    outName_gr = rutavectores + "\\" + 'Grilla_'+str(idc)+'.shp'
		    inFeatures_pc = ["grillac", "incs"]
		    arcpy.Intersect_analysis(inFeatures_pc, outName_gr)
		    #Medida DTM Distorsion Geometrica
		    sql = "Tipo_Error = 1 OR Tipo_Error = 4 OR Tipo_Error = 5"
		    arcpy.MakeFeatureLayer_management(outName_gr, "grillacs")
		    arcpy.SelectLayerByAttribute_management("grillacs", "NEW_SELECTION", sql)
		    exp = "!SHAPE.AREA@HECTARES!"
		    arcpy.CalculateField_management("grillacs", "Area", exp, "PYTHON_9.3")
		    salidar = rutavectores + "\\tabla"+str(idc)
		    arcpy.Statistics_analysis("grillacs", salidar, [["Area", "SUM"]])
		    cursor = arcpy.da.SearchCursor(salidar, ["SUM_AREA"])
		    data=[row for row in cursor]
		    if data == []:
		        newsheet.write(k,1,0)
		    else:
		        newsheet.write(k,1,round(data[0][0],3))
		    #arcpy.Delete_management(salidar)
		    #Medida RAD Desbalance Radiometrico
		    sql = "Tipo_Error = 3"
		    arcpy.SelectLayerByAttribute_management("grillacs", "NEW_SELECTION", sql)
		    exp = "!SHAPE.AREA@HECTARES!"
		    arcpy.CalculateField_management("grillacs", "Area", exp, "PYTHON_9.3")
		    salidar2 = rutavectores + "\\tabla2"+str(idc)
		    arcpy.Statistics_analysis("grillacs", salidar2, [["Area", "SUM"]])
		    cursor = arcpy.da.SearchCursor(salidar2, ["SUM_AREA"])
		    data=[row for row in cursor]
		    if data == []:
		        newsheet.write(k,2,0)
		    else:
		        newsheet.write(k,2,round(data[0][0],3))
		    
		    arcpy.Delete_management(salidar)
		    arcpy.Delete_management(salidar2)
		    arcpy.Delete_management(outName_gr)
		    arcpy.Delete_management("grillac")
		    arcpy.Delete_management("grillacs")
		    k+=1

		wbg.save(rutavectores+"\\"+'Grilla_Inconsistencias'+nameimagen+'.xls')

	arcpy.Delete_management("incs")
	arcpy.Delete_management(salida2)


else:	
	f = open(txtdrv, "r")
	content = f.read()
	#Extraer punto
	posp = content.find("Point")
	trmspx = content[posp:posp+201]
	trmspy = content[posp:posp+217]
	trmspx2 = trmspx.split(" ")
	trmspy2 = trmspy.split(" ")
	cordx = trmspx2[-1].replace(',','.')
	cordy = trmspy2[-1].replace(',','.')
	spatial_reference = arcpy.Describe(inconsistenciasv).spatialreference
	fcp = rutavectores + "\\" + "Pointval.shp"
	print(cordx)
	print(cordy)
	point = arcpy.PointGeometry(arcpy.Point(float(cordx),float(cordy)),spatial_reference)
	arcpy.CopyFeatures_management(point, fcp)
	Area_intp = rutavectores + "\\" + 'AreaTPr_'+nameimagen.replace('-','')+'.shp'
	inFeaturesi = [fcp, Area_intp]
	outName_int = rutavectores + "\\" + 'Pint_'+nameimagen.replace('-','')+'.shp'
	arcpy.Intersect_analysis(inFeaturesi, outName_int)
	layerCount = int(arcpy.GetCount_management(outName_int).getOutput(0))
	if layerCount==0:
		print('Los puntos del RMSE no coinciden con el area del proyecto')
		print('Terminando Script...')
	else:
		#Extraer RMSE
		pos1 = content.find("RMSE")
		trmse = content[pos1:pos1+14]
		trms2 = trmse.split("\t")
		valrmse = trms2[4]
		print("Valor del RMSE ",valrmse)
		ws.write(19,28,str(valrmse))
		wsrv.write(7, 1, str(valrmse), style0)
		if(float(valrmse.replace(',','.')) <= umbrale):
			ws.write(19,30,"CONFORME")
		else:
			ws.write(19,30,"NO CONFORME")

		#Medida LC Empalme
		sql = "Tipo_Error = 2"
		arcpy.MakeFeatureLayer_management(inconsistenciasv, "incs")
		arcpy.SelectLayerByAttribute_management("incs", "NEW_SELECTION", sql)
		salida2 = rutavectores + "\\tablainc2"
		exp = "!SHAPE.AREA@HECTARES!"
		arcpy.CalculateField_management("incs", "Area", exp, "PYTHON_9.3")
		#Sumar areas de registros
		arcpy.Statistics_analysis("incs", salida2, [["Area", "SUM"]])
		cursor = arcpy.da.SearchCursor(salida2, ["SUM_AREA"])
		data=[row for row in cursor]
		if data == []:
			print('El numero de pixeles de Empalme es 0')
			npixel = 0
		else:
			emp = data[0][0]
			empm = float(emp)*10000
			npixel = empm/(respacial*respacial)
			print('El numero de pixeles por empalme es ',npixel)
		ws.write(20,28,str(int(npixel)))
		if npixel > 2:
			ws.write(20,32,'No cumple')
			ws.write(20,30,"NO CONFORME")
		else:
			ws.write(20,32,'Cumple')
			ws.write(20,30,"CONFORME")
		wsrv.write(8, 1, str(npixel), style0)

		arcpy.Delete_management("incs")

		if tmuestreo==1:
			#Calculo medidas de consistencia
			inconsistenciasv = rutavectores + "\\"+ rutainct +"\Inconsistencia\Inconsistencias_Orto"
			arcpy.MakeFeatureLayer_management(inconsistenciasv, "incs")
			#Medida DTM Distorsion Geometrica
			sql = "Tipo_Error = 1 OR Tipo_Error = 4 OR Tipo_Error = 5"
			arcpy.SelectLayerByAttribute_management("incs", "NEW_SELECTION", sql)
			salida1 = rutavectores + "\\tablainc1"
			exp = "!SHAPE.AREA@HECTARES!"
			arcpy.CalculateField_management("incs", "Area", exp, "PYTHON_9.3")
			#Sumar areas de registros
			arcpy.Statistics_analysis("incs", salida1, [["Area", "SUM"]])
			field_names = [i.name for i in arcpy.ListFields(salida1) if i.type != 'OID']
			cursor = arcpy.da.SearchCursor(salida1, ["SUM_AREA"])
			data=[row for row in cursor]
			if data == []:
				print('El area de Distorsion Geometrica es 0')
				dg = 0
			else:
				dg = data[0][0]	
			prcdg = (dg/areaproyecto)*100
			print('El area de Distorsion Geometrica es ',dg, ' corresponde a ',str(round(prcdg,2)), '%')
			ws.write(21,28,str(round(prcdg,2)))
			wsrv.write(9, 1, str(round(prcdg,2)), style0)
			if(prcdg<=1):
				ws.write(21,30,"CONFORME")
			else:
				ws.write(21,30,"NO CONFORME")

			#Medida RAD Desbalance Radiometrico
			sql = "Tipo_Error = 3"
			arcpy.SelectLayerByAttribute_management("incs", "NEW_SELECTION", sql)
			salida3 = rutavectores + "\\tablainc3"
			exp = "!SHAPE.AREA@HECTARES!"
			arcpy.CalculateField_management("incs", "Area", exp, "PYTHON_9.3")
			#Sumar areas de registros
			arcpy.Statistics_analysis("incs", salida3, [["Area", "SUM"]])
			cursor = arcpy.da.SearchCursor(salida3, ["SUM_AREA"])
			data=[row for row in cursor]
			if data == []:
				print('El area de Desbalance Radiometrico es 0')
				dr = 0
			else:
				dr = data[0][0]
			prcdr = (dr/areaproyecto)*100
			print('El area de Desbalance Radiometrico es ',dr, ' corresponde a ',str(round(prcdr,2)), '%')
			ws.write(22,28,str(round(prcdr,2)))
			wsrv.write(10, 1, str(round(prcdr,2)), style0)
			if(prcdr<=1):
				ws.write(22,30,"CONFORME")
			else:
				ws.write(22,30,"NO CONFORME")

			arcpy.Delete_management(salida1)
			arcpy.Delete_management(salida3)
		else:
			ngrilla = "MarcosCS_"+ nameimagen.replace('-','')
			grilla = rutavectores + "\\"+ ngrilla +".shp"
			ws.write(21,32,'Medida calculada con grilla')
			ws.write(22,32,'Medida calculada con grilla')
			wsrv.write(9, 1, 'Medida calculada con grilla', style0)
			wsrv.write(10, 1, 'Medida calculada con grilla', style0)
			ws.write(21,30,"")
			ws.write(22,30,"")
			inconsistenciasv = rutavectores + "\\"+ rutainct +"\Inconsistencia\Inconsistencias_Orto"
			arcpy.MakeFeatureLayer_management(inconsistenciasv, "incs")
			field_names = [i.name for i in arcpy.ListFields(grilla) if i.type != 'OID']
			cursor = arcpy.da.SearchCursor(grilla, field_names)
			wbg = xlwt.Workbook() # create empty workbook object
			newsheet = wbg.add_sheet('Grillas')
			newsheet.write(0,0,'Id_Grilla')
			newsheet.write(0,1,'Distorsion_geometrica')
			newsheet.write(0,2,'Desbalance_radiometrico')
			k=1
			for row in cursor:
			    idc = row[1]
			    exp = "Id="+str(idc)
			    print('Calculando Grilla Id: ',idc)
			    newsheet.write(k,0,idc)
			    arcpy.MakeFeatureLayer_management(grilla, "grillac")
			    arcpy.SelectLayerByAttribute_management("grillac","NEW_SELECTION",exp)
			    outName_gr = rutavectores + "\\" + 'Grilla_'+str(idc)+'.shp'
			    inFeatures_pc = ["grillac", "incs"]
			    arcpy.Intersect_analysis(inFeatures_pc, outName_gr)
			    #Medida DTM Distorsion Geometrica
			    sql = "Tipo_Error = 1 OR Tipo_Error = 4 OR Tipo_Error = 5"
			    arcpy.MakeFeatureLayer_management(outName_gr, "grillacs")
			    arcpy.SelectLayerByAttribute_management("grillacs", "NEW_SELECTION", sql)
			    exp = "!SHAPE.AREA@HECTARES!"
			    arcpy.CalculateField_management("grillacs", "Area", exp, "PYTHON_9.3")
			    salidar = rutavectores + "\\tabla"+str(idc)
			    arcpy.Statistics_analysis("grillacs", salidar, [["Area", "SUM"]])
			    cursor = arcpy.da.SearchCursor(salidar, ["SUM_AREA"])
			    data=[row for row in cursor]
			    if data == []:
			        newsheet.write(k,1,0)
			    else:
			        newsheet.write(k,1,round(data[0][0],3))
			    #arcpy.Delete_management(salidar)
			    #Medida RAD Desbalance Radiometrico
			    sql = "Tipo_Error = 3"
			    arcpy.SelectLayerByAttribute_management("grillacs", "NEW_SELECTION", sql)
			    exp = "!SHAPE.AREA@HECTARES!"
			    arcpy.CalculateField_management("grillacs", "Area", exp, "PYTHON_9.3")
			    salidar2 = rutavectores + "\\tabla2"+str(idc)
			    arcpy.Statistics_analysis("grillacs", salidar2, [["Area", "SUM"]])
			    cursor = arcpy.da.SearchCursor(salidar2, ["SUM_AREA"])
			    data=[row for row in cursor]
			    if data == []:
			        newsheet.write(k,2,0)
			    else:
			        newsheet.write(k,2,round(data[0][0],3))
			    
			    arcpy.Delete_management(salidar)
			    arcpy.Delete_management(salidar2)
			    arcpy.Delete_management(outName_gr)
			    arcpy.Delete_management("grillac")
			    arcpy.Delete_management("grillacs")
			    k+=1

			wbg.save(rutavectores+"\\"+'Grilla_Inconsistencias'+nameimagen+'.xls')

		arcpy.Delete_management("incs")
		arcpy.Delete_management(salida2)


	arcpy.Delete_management(outName_int)
	arcpy.Delete_management(fcp)



#Guardar Excel
print('Guardando Excel')
ruta = directorioe.split("\\")
rnew = ruta[:-1]
sep = "\\"
rutanueva = sep.join(rnew)
namearc = ruta[-1].split(".")[0]
wb.save(rutavectores+'\\'+namearc+'_v2.xls')
wbrv.save(rutavectores+'\\'+excelrv+'_vf.xls')
print("Reporte V2 Guardado")


#Borrar archivos temporales
print '\n'


#arcpy.Delete_management(salidanub)
#arcpy.Delete_management(image_band_1_out)
arcpy.ClearWorkspaceCache_management()

