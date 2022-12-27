import statistics
import arcpy
import random
from arcpy import env
from arcpy.arcobjects.arcobjects import Result
from arcpy.sa import *
import os, re
import requests
import time
import argparse
import sys
import time
import math
from datetime import datetime
import unicodedata
#reload(sys)
#sys.setdefaultencoding('utf8')
# import comtypes
# from comtypes.client import GetModule
# from comtypes.client import CreateObject
#GeodatabaseEntrada=sys.argv[1]
#GeodatabaseSalida=sys.argv[2]
GeodatabaseEntrada=arcpy.GetParameterAsText(0)
foldersalida = arcpy.GetParameterAsText(1)
GeodatabaseSalida=arcpy.GetParameterAsText(2)
GeodatabaseSalida=foldersalida+"\\"+GeodatabaseSalida+".gdb"
escala = arcpy.GetParameterAsText(4)
#Xml=sys.argv[6]
Script = arcpy.GetParameterAsText(5)
arcpy.env.overwriteOutput=True;
arcpy.CheckOutExtension("Spatial")
areas = {"1000":50, "2000":100, "5000":250, "10000":500, "25000":1000,"50000":2500,"100000":4000}
ruta = GeodatabaseSalida.split("\\")
rnew = ruta[:-1]
sep = "\\"
rutasal = sep.join(rnew)
namem = ruta[-1].split('.')[0]
rutasalida = rutasal + "\\" + namem
arcpy.AddMessage("Guardando Resultados en: "+rutasalida)
os.mkdir(rutasalida)
filet = open(rutasalida+"\\"+"Report_"+namem+".txt","a")
filet.write("---REPORTE DEL SCRIPT PARA LA GDB "+namem+ "-----\n")
if arcpy.GetParameterAsText(3) == '#':
    inFeatures = os.path.join(GeodatabaseEntrada, 'Elevacion', 'CNivel')
    outFeatureClass = os.path.join(rutasal, namem +"_AC.shp")
    result = int(arcpy.GetCount_management(inFeatures).getOutput(0))
    arcpy.AddMessage("No se especifico area de corte, se calculara usando los datos de las curvas de nivel")
    if result > 0:
        arcpy.MinimumBoundingGeometry_management(inFeatures, outFeatureClass, "CONVEX_HULL", "ALL")
        ShapefileCorte=outFeatureClass
    else:
        arcpy.AddMessage("No hay datos sufifientes para calcular el area de corte, por favor generela manuelmente")
else:
    ShapefileCorte=arcpy.GetParameterAsText(3)
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
if Script == 'MARCOS_100':
    arcpy.AddMessage('MARCOS_100')
    def SelectRandomByCount(layer, count, salidapuntos):
        layerCount = int(arcpy.GetCount_management(layer).getOutput(0))
        if layerCount < count:
            print ("NO EXISTEN SUFICIENTES PUNTOS PARA SELECIONAR")
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
    arcpy.CreateFileGDB_management(os.path.dirname(GeodatabaseSalida),os.path.basename(GeodatabaseSalida))
    #####################
    #arcpy.FeatureClassToFeatureClass_conversion(ShapefileCorte,GeodatabaseEntrada + "\\Indice_Mapas","CORTE" )
    CORTE = ShapefileCorte
    arcpy.AddMessage("Cortando Geodatabase")
    arcpy.env.workspace = GeodatabaseEntrada
    datasetList = arcpy.ListDatasets()
    for dataset in datasetList:
        if(dataset!="IndiceMapas" and dataset!="OrdenamientoTerritorial"):
            arcpy.AddMessage('Analizando Dataset '+dataset+' Esta entrando aca!!')
            filet.write('Analizando Dataset '+dataset + "\n")
            arcpy.AddMessage(str(GeodatabaseEntrada) + "\\" + str(dataset))
            arcpy.env.workspace = GeodatabaseEntrada + "\\" + dataset
            descd = arcpy.Describe(GeodatabaseEntrada + "\\" + dataset)
            sr = descd.spatialreference
            arcpy.CreateFeatureDataset_management(GeodatabaseSalida, dataset, sr)
            fcList = arcpy.ListFeatureClasses()
            for fc in fcList:
                result = int(arcpy.GetCount_management(fc).getOutput(0))
                try:
                    if result>0:
                        #if(fc!="Bosque" and fc!="Cerca"):
                        arcpy.AddMessage('Cortando FeatureClass '+fc)
                        filet.write("Corte del Feature "+fc + "\n")
                        fcSal=GeodatabaseSalida + "\\" + dataset + "\\" + fc
                        desc = arcpy.Describe(fc)
                        if(desc.featureType!="Annotation"):
                            if(arcpy.Exists(fc+"_Anot")):
                                arcpy.Clip_analysis(fc+"_Anot", CORTE , fcSal+"_Anot")
                            arcpy.Clip_analysis(fc, CORTE , fcSal)
                except Exception as ex:
                    arcpy.AddMessage("Error..."+ex.message)
    del datasetList
    del fcList
    arcpy.AddMessage("GDB Cortada...")
    arcpy.AddMessage("Generando grilla...")
    valesc = areas[str(escala)]
    sptref = arcpy.Describe(ShapefileCorte).spatialreference
    extent = arcpy.Describe(ShapefileCorte).extent
    arcpy.env.outputCoordinateSystem = sptref
    coords = str(extent.XMin) + " " + str(extent.YMin)
    yAxisCoordinate = str(extent.XMin) + " " + str(extent.YMin+1)
    oppositeCoorner = str(extent.XMax) + " " + str(extent.YMax)
    outpg = rutasalida + "\\" + 'MarcosAT' + namem + '.shp'
    arcpy.CreateFishnet_management(outpg, coords, yAxisCoordinate, valesc, valesc, "0", "0", oppositeCoorner, "NO_LABELS", "", "POLYGON")
    resultgr = int(arcpy.GetCount_management(outpg).getOutput(0))
    arcpy.AddMessage("Grilla Total Generada con "+str(resultgr)+" celdas...")
    filet.write("Grilla Total Generada con "+str(resultgr)+" celdas..." + "\n")
    #Interseccion Area Proyecto
    salidagrillai = rutasalida + "\\" + 'MarcosInt_'+namem.replace('-','')+'.shp'
    arcpy.MakeFeatureLayer_management (outpg, "grillat")
    arcpy.management.SelectLayerByLocation("grillat", "WITHIN", ShapefileCorte) ##Verificar que en este punto se haga la selección dentro Punto 6, se modifico la función de selección por python 3
    arcpy.CopyFeatures_management("grillat", salidagrillai)
    #arcpy.AddField_management(salidagrillai, "Id", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
    expression = "autoIncrement()"
    arcpy.CalculateField_management(salidagrillai, "Id", expression, "PYTHON_9.3", codeblock)
    arcpy.AddField_management(salidagrillai, "Num_elm", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
    resultgri = int(arcpy.GetCount_management(salidagrillai).getOutput(0))
    arcpy.AddMessage("Grilla Intersectada con area de trabajo, "+str(resultgri)+" celdas...")
    filet.write("Grilla Intersectada con area de trabajo, "+str(resultgri)+" celdas..." + "\n")
    arcpy.Delete_management("grillat")
    field_names = [i.name for i in arcpy.ListFields(salidagrillai) if i.type != 'OID']
    cursor = arcpy.da.SearchCursor(salidagrillai, field_names)
    numelementos = 0
    numelementos_bacm = 0
    for row in cursor:
        idc = row[1]
        exp = "Id="+str(idc)
        arcpy.AddMessage('Calculando Grilla Id: '+ str(idc))
        filet.write('Calculando Grilla Id: '+ str(idc) + "\n")
        arcpy.MakeFeatureLayer_management(salidagrillai, "grillac")
        arcpy.SelectLayerByAttribute_management("grillac","NEW_SELECTION",exp)
        arcpy.env.workspace = GeodatabaseSalida
        datasetList = arcpy.ListDatasets()
        numcapas = 0
        numcapas_bacm = 0
        for dataset in datasetList:
            arcpy.env.workspace = GeodatabaseSalida + "\\" + dataset
            fcList = arcpy.ListFeatureClasses()
            for fc in fcList:
                outName_gr = rutasalida + "\\" + 'Gr_'+str(idc)+str(fc)+'.shp'
                inFeatures_pc = ["grillac", fc]
                arcpy.Intersect_analysis(inFeatures_pc, outName_gr)
                result = int(arcpy.GetCount_management(outName_gr).getOutput(0))
                arcpy.AddMessage("El numero de elementos de "+str(fc)+" es: "+str(result))
                filet.write("El numero de elementos de "+str(fc)+" es: "+str(result) + "\n")
                if (str(fc) == 'Bosque' or str(fc) == 'Cerca'):
                    numcapas_bacm += result
                else:
                    numcapas += result
                arcpy.Delete_management(outName_gr)
        arcpy.CalculateField_management("grillac", "Num_elm", numcapas, "PYTHON_9.3")
        arcpy.AddMessage("El numero de elementos en la grilla "+ str(idc)+" categoria otros es: "+ str(numcapas))
        arcpy.AddMessage("El numero de elementos en la grilla "+ str(idc)+" categoria bacm es: "+ str(numcapas_bacm))
        filet.write("El numero de elementos en la grilla "+ str(idc)+" categoria otros es: "+ str(numcapas) + "\n")
        filet.write("El numero de elementos en la grilla "+ str(idc)+" categoria bacm es: "+ str(numcapas_bacm) + "\n")
        arcpy.Delete_management("grillac")
        numelementos += numcapas
        numelementos_bacm += numcapas_bacm
    arcpy.AddMessage("El numero de elementos categoria otros en todas las celdas es "+ str(numelementos))
    arcpy.AddMessage("El numero de elementos categoria bacm en todas las celdas es "+ str(numelementos_bacm))
    filet.write("El numero de elementos categoria otros en todas las celdas es "+ str(numelementos) + "\n")
    filet.write("El numero de elementos categoria bacm en todas las celdas es "+ str(numelementos_bacm) + "\n")
    arcpy.Delete_management("grillac")
    salidatb = rutasalida + "\\tablagr.txt"
    #Sumar areas del area del proyecto
    arcpy.Statistics_analysis(salidagrillai, salidatb, [["Num_elm", "SUM"]])
    field_namespr = [i.name for i in arcpy.ListFields(salidatb) if i.type != 'OID']
    cursorpr = arcpy.da.SearchCursor(salidatb, field_namespr)
    datapr =[row for row in cursorpr]
    numel_total = datapr[0][2]
    result= arcpy.GetCount_management(salidagrillai)
    numel_gr = int(result.getOutput(0))
    pr_elmgr = numel_total/numel_gr
    count = int(numel_total)
    z = 1.96
    if numelementos < numelementos_bacm:
        p = 0.05
        arcpy.AddMessage("Voy a usar p 0.05")
    else:
        p = 0.03
        arcpy.AddMessage("Voy a usar p 0.03")
    e = 0.01
    a = (z*z)*(p)*(1-p)
    b = (e*e)
    c = (count-1)/ float(count)
    d = count*(e*e)
    ef = a/d
    f = c + ef
    g = a/b
    o = g/f
    n = int(o)
    num_mr = int(math.ceil(n/pr_elmgr))
    arcpy.AddMessage("Tamano de muestra minimo en elementos "+str(n))
    filet.write("\n \n")
    filet.write("Tamano de muestra minimo en elementos "+str(n) + "\n")
    if num_mr <= 15:
        arcpy.AddMessage("El numero de marcos obtenidos es "+str(num_mr)+ " se dejaran todos los marcos inicialmente generados, "+ str(numel_gr))
        filet.write("El numero de marcos obtenidos es "+str(num_mr)+ " se dejaran todos los marcos inicialmente generados, "+ str(numel_gr) + "\n")
    else:
        arcpy.AddMessage("El numero de marcos obtenidos es "+str(num_mr)+ ", se extraera dicha cantidad de marcos.")
        filet.write("El numero de marcos obtenidos es "+str(num_mr)+ ", se extraera dicha cantidad de marcos." + "\n")
        arcpy.AddMessage("Generando Marcos Aleatorios..")
        # outName = 'PuntosA.shp'
        # arcpy.CreateRandomPoints_management(rutasalida, outName, ShapefileCorte, "", num_mr, valesc)
        # arcpy.MakeFeatureLayer_management (outpg, "grillati")
        # arcpy.SelectLayerByLocation_management("grillati", "intersect", rutasalida+"\\"+outName)
        # salidagrillap = rutasalida + "\\" + 'MarcosCS_'+namem.replace('-','')+'.shp'
        # arcpy.CopyFeatures_management("grillati", salidagrillap)
        out_points = rutasalida + "\\" + 'MarcosCS_'+namem.replace('-','')+'.shp'
        SelectRandomByCount(salidagrillai,num_mr,out_points)
        arcpy.AddMessage("Marcos de control generados")
        filet.write("Marcos de control generados" + "\n")
        # arcpy.Delete_management("grillati")
        # arcpy.Delete_management(rutasalida+"\\"+outName)
    arcpy.Delete_management(salidatb)
    filet.close()    
else:
    arcpy.AddMessage('MARCOS')
    def SelectRandomByCount(layer, count, salidapuntos):
        layerCount = int(arcpy.GetCount_management(layer).getOutput(0))
        if layerCount < count:
            print ("NO EXISTEN SUFICIENTES PUNTOS PARA SELECIONAR")
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
    arcpy.CreateFileGDB_management(os.path.dirname(GeodatabaseSalida),os.path.basename(GeodatabaseSalida))
    #####################
    #arcpy.FeatureClassToFeatureClass_conversion(ShapefileCorte,GeodatabaseEntrada + "\\Indice_Mapas","CORTE" )
    CORTE = ShapefileCorte
    arcpy.AddMessage("Cortando Geodatabase")
    arcpy.env.workspace = GeodatabaseEntrada
    datasetList = arcpy.ListDatasets()
    for dataset in datasetList:
        if(dataset!="IndiceMapas" and dataset!="OrdenamientoTerritorial"):
            arcpy.AddMessage('Analizando Dataset '+dataset+' Esta entrando aca 2')
            filet.write('Analizando Dataset '+dataset + "\n")
            arcpy.AddMessage("Entrada: "+GeodatabaseEntrada + "\\" + dataset)
            arcpy.AddMessage("Salida: "+GeodatabaseSalida + "\\" + dataset)
            arcpy.env.workspace = r""+GeodatabaseEntrada + "\\" + dataset
            descd = arcpy.Describe(GeodatabaseEntrada + "\\" + dataset)
            sr = descd.spatialreference
            arcpy.CreateFeatureDataset_management(GeodatabaseSalida, dataset, sr)
            fcList = arcpy.ListFeatureClasses()
            for fc in fcList:
                result = int(arcpy.GetCount_management(fc).getOutput(0))
                try:
                    if result>0:
                        #if(fc!="Bosque" and fc!="Cerca"):
                        arcpy.AddMessage('Cortando FeatureClass '+fc)
                        filet.write("Corte del Feature "+fc + "\n")
                        fcSal=GeodatabaseSalida + "\\" + dataset + "\\" + fc
                        desc = arcpy.Describe(fc)
                        if(desc.featureType!="Annotation"):
                            if(arcpy.Exists(fc+"_Anot")):
                                arcpy.Clip_analysis(fc+"_Anot", CORTE , fcSal+"_Anot")
                            arcpy.Clip_analysis(fc, CORTE , fcSal)
                except Exception as ex:
                    arcpy.AddMessage("Error..."+ex.message)
    del datasetList
    del fcList
    arcpy.AddMessage("GDB Cortada...")
    arcpy.AddMessage("Generando grilla...")
    valesc = areas[str(escala)]
    sptref = arcpy.Describe(ShapefileCorte).spatialreference
    extent = arcpy.Describe(ShapefileCorte).extent
    arcpy.env.outputCoordinateSystem = sptref
    coords = str(extent.XMin) + " " + str(extent.YMin)
    yAxisCoordinate = str(extent.XMin) + " " + str(extent.YMin+1)
    oppositeCoorner = str(extent.XMax) + " " + str(extent.YMax)
    outpg = rutasalida + "\\" + 'MarcosAT' + namem + '.shp'
    arcpy.CreateFishnet_management(outpg, coords, yAxisCoordinate, valesc, valesc, "0", "0", oppositeCoorner, "NO_LABELS", "", "POLYGON")
    resultgr = int(arcpy.GetCount_management(outpg).getOutput(0))
    arcpy.AddMessage("Grilla Total Generada con "+str(resultgr)+" celdas...")
    filet.write("Grilla Total Generada con "+str(resultgr)+" celdas..." + "\n")
    #Interseccion Area Proyecto
    salidagrillain = rutasalida + "\\" + 'MarcosInt_'+namem.replace('-','')+'.shp'
    arcpy.MakeFeatureLayer_management (outpg, "grillat")
    arcpy.SelectLayerByLocation_management("grillat", "WITHIN", ShapefileCorte) #Punto 7, generación de marcos Internos 
    arcpy.CopyFeatures_management("grillat", salidagrillain)
    #arcpy.AddField_management(salidagrillai, "Id", "DOUBLE", 0, "", "", "", "NULLABLE", "REQUIRED")
    expression = "autoIncrement()"
    arcpy.CalculateField_management(salidagrillain, "Id", expression, "PYTHON_9.3", codeblock)
    arcpy.AddField_management(salidagrillain, "Num_elm", "DOUBLE", 0, "", "", "", "NULLABLE", "NON_REQUIRED")
    resultgri = int(arcpy.GetCount_management(salidagrillain).getOutput(0))
    arcpy.AddMessage("Grilla Intersectada con area de trabajo, "+str(resultgri)+" celdas...")
    filet.write("Grilla Intersectada con area de trabajo, "+str(resultgri)+" celdas..." + "\n")
    arcpy.Delete_management("grillat")
    ######poner en bucle 20 veces
    #if resultgri>30:
    #    arcpy.AddMessage("Se seleccionaran 30 marcos de los "+str(resultgri)+" intersectados...")
    #    filet.write("Se seleccionaran 30 marcos de los "+str(resultgri)+" intersectados..." + "\n")
    numelementos_total = 0
    numelementos_bacm_total = 0
    promedio = []
    promedio_bacm = []
    for i in range(20):
        arcpy.AddMessage('Ejecutando el ciclo No. '+ str(i+1))
        filet.write('Ejecutando el ciclo No. '+ str(i+1) + "\n")
        salidagrillai = rutasalida + "\\" + 'Marcos10_'+namem.replace('-','')+'.shp'
        SelectRandomByCount(salidagrillain,10,salidagrillai)
        #else:
        #    salidagrillai = rutasalida + "\\" + 'MarcosInt_'+namem.replace('-','')+'.shp'
        field_names = [i.name for i in arcpy.ListFields(salidagrillai) if i.type != 'OID']
        cursor = arcpy.da.SearchCursor(salidagrillai, field_names)
        numelementos = 0
        numelementos_bacm = 0
        for row in cursor:
            idc = row[1]
            exp = "Id="+str(idc)
            arcpy.AddMessage('Calculando Grilla Id: '+ str(idc))
            filet.write('Calculando Grilla Id: '+ str(idc) + "\n")
            arcpy.MakeFeatureLayer_management(salidagrillai, "grillac")
            arcpy.SelectLayerByAttribute_management("grillac","NEW_SELECTION",exp)
            arcpy.env.workspace = GeodatabaseSalida
            datasetList = arcpy.ListDatasets()
            numcapas = 0
            numcapas_bacm = 0
            for dataset in datasetList:
                arcpy.env.workspace = GeodatabaseSalida + "\\" + dataset
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    outName_gr = rutasalida + "\\" + 'Gr_'+str(idc)+str(fc)+'.shp'
                    inFeatures_pc = ["grillac", fc]
                    arcpy.Intersect_analysis(inFeatures_pc, outName_gr)
                    result = int(arcpy.GetCount_management(outName_gr).getOutput(0))
                    arcpy.AddMessage("El numero de elementos de "+str(fc)+" es: "+str(result))
                    filet.write("El numero de elementos de "+str(fc)+" es: "+str(result) + "\n")
                    if (str(fc) == 'Bosque' or str(fc) == 'Cerca'):
                        numcapas_bacm += result
                    else:
                        numcapas += result
                    arcpy.Delete_management(outName_gr)
            arcpy.CalculateField_management("grillac", "Num_elm", numcapas, "PYTHON_9.3")
            arcpy.AddMessage("El numero de elementos en la grilla "+ str(idc)+" categoria otros es: "+ str(numcapas))
            arcpy.AddMessage("El numero de elementos en la grilla "+ str(idc)+" categoria bacm es: "+ str(numcapas_bacm))
            filet.write("El numero de elementos en la grilla "+ str(idc)+" categoria otros es: "+ str(numcapas) + "\n")
            filet.write("El numero de elementos en la grilla "+ str(idc)+" categoria bacm es: "+ str(numcapas_bacm) + "\n")
            arcpy.Delete_management("grillac")
            numelementos += numcapas
            numelementos_bacm += numcapas_bacm
        arcpy.AddMessage("El numero de elementos categoria otros en todas las celdas es "+ str(numelementos))
        arcpy.AddMessage("El numero de elementos categoria bacm en todas las celdas es "+ str(numelementos_bacm))
        filet.write("El numero de elementos categoria otros en todas las celdas es "+ str(numelementos) + "\n")
        filet.write("El numero de elementos categoria bacm en todas las celdas es "+ str(numelementos_bacm) + "\n")
        arcpy.Delete_management("grillac")
        promedio.append((numelementos*1.0)/10)
        promedio_bacm.append((numelementos_bacm*1.0)/10)
        arcpy.AddMessage("El numero de elementos promedio en la categoria otros en esta iteracion es "+ str((numelementos*1.0)/10))
        arcpy.AddMessage("El numero de elementos promedio en la categoria bacm en esta iteracion es "+ str((numelementos_bacm*1.0)/10))
        filet.write("El numero de elementos promedio en la categoria otros en esta iteracion es "+ str((numelementos*1.0)/10) + "\n")
        filet.write("El numero de elementos promedio en la categoria bacm en esta iteracion es "+ str((numelementos_bacm*1.0)/10) + "\n")
        numelementos_total += numelementos
        numelementos_bacm_total += numelementos_bacm
    arcpy.AddMessage("************************ LOS RESULTADOS SON **************************")
    filet.write("************************ LOS RESULTADOS SON **************************" + "\n")
    arcpy.AddMessage("El numero de elementos categoria otros en todos los ciclos es "+ str(numelementos_total))
    arcpy.AddMessage("El numero de elementos categoria bacm en todos los ciclos es "+ str(numelementos_bacm_total))
    filet.write("El numero de elementos categoria otros en todos los ciclos es "+ str(numelementos_total) + "\n")
    filet.write("El numero de elementos categoria bacm en todos los ciclos es "+ str(numelementos_bacm_total) + "\n")
    mean_otros = sum(promedio)/len(promedio)
    mean_bacm = sum(promedio_bacm)/len(promedio_bacm)
    desv_otros = statistics.pstdev(promedio)
    #arcpy.AddMessage("La desviacion de la categoria otros es: " + str(desv_otros))
    desv_bacm = statistics.pstdev(promedio_bacm)
    lim_sup_total_otros = mean_otros + 1.65 * (desv_otros/math.sqrt(20))
    lim_sup_total_bacm = mean_bacm + 1.65 * (desv_bacm/math.sqrt(20))
    if numelementos_total < numelementos_bacm_total:
        arcpy.AddMessage("El mayor conteo de elementos fue en la categoria bacm y se usará un p de 0.05 ")
        p = 0.05
        count = int (numelementos_bacm_total)
        pr_elmgr = int (math.ceil(lim_sup_total_bacm))
    else:
        arcpy.AddMessage("El mayor conteo de elementos fue en la categoria otros y se usará un p de 0.03 ")
        p = 0.03
        count = int(numelementos_total)
        pr_elmgr = int (math.ceil(lim_sup_total_otros))
    arcpy.AddMessage("-----------------------------------------------------------------------------")
    filet.write("---------------------------------------------------------------------------" + "\n")
    arcpy.AddMessage("El numero promedio de elementos en la categoria otros es "+ str(mean_otros))
    arcpy.AddMessage("El numero promedio de elementos en la categoria bacm es "+ str(mean_bacm))
    filet.write("El numero promedio de elementos en la categoria otros es "+ str(mean_otros) + "\n")
    filet.write("El numero promedio de elementos en la categoria bacm es "+ str(mean_bacm) + "\n")
    arcpy.AddMessage("-----------------------------------------------------------------------------")
    filet.write("---------------------------------------------------------------------------" + "\n")
    arcpy.AddMessage("El limite superior para la categoria otros es "+ str(round(lim_sup_total_otros)))
    arcpy.AddMessage("El limite superior para la categoria bacm es "+ str(round(lim_sup_total_bacm)))
    filet.write("El limite superior para la categoria otros es "+ str(round(lim_sup_total_otros)) + "\n")
    filet.write("El limite superior para la categoria bacm es "+ str(round(lim_sup_total_bacm)) + "\n")
    salidatb = rutasalida + "\\tablagr.txt"
    #Sumar areas del area del proyecto
    arcpy.Statistics_analysis(salidagrillai, salidatb, [["Num_elm", "SUM"]])
    field_namespr = [i.name for i in arcpy.ListFields(salidatb) if i.type != 'OID']
    cursorpr = arcpy.da.SearchCursor(salidatb, field_namespr)
    datapr =[row for row in cursorpr]
    numel_total = datapr[0][2]
    result= arcpy.GetCount_management(salidagrillai)
    numel_gr = int(result.getOutput(0))
    '''pr_elmgr = numel_total/numel_gr
    #pr_elmgr = numel_total/200
    numel_totales = pr_elmgr*resultgri'''
    # arcpy.AddMessage("numel_total es: "+ str(numel_total))
    # arcpy.AddMessage("numel_totales es: "+ str(numel_totales))
    '''count = int(numel_totales)'''
    z = 1.96
    e = 0.01
    a = (z*z)*(p)*(1-p)
    b = (e*e)
    c = (count-1)/ float(count)
    d = count*(e*e)
    ef = a/d
    f = c + ef
    g = a/b
    o = g/f
    n = int(math.ceil(o))
    num_mr = int(math.ceil(n/pr_elmgr))
    arcpy.AddMessage("Tamano de muestra minimo en elementos "+str(n))
    filet.write("\n \n")
    filet.write("Tamano de muestra minimo en elementos "+str(n) + "\n")
    if num_mr <= 15:
        arcpy.AddMessage("El numero de marcos obtenidos es "+str(num_mr)+ " se dejaran todos los marcos inicialmente generados, "+ str(numel_gr))
        filet.write("El numero de marcos obtenidos es "+str(num_mr)+ " se dejaran todos los marcos inicialmente generados, "+ str(numel_gr) + "\n")
    else:
        arcpy.AddMessage("El numero de marcos obtenidos es "+str(num_mr)+ ", se extraera dicha cantidad de marcos.")
        filet.write("El numero de marcos obtenidos es "+str(num_mr)+ ", se extraera dicha cantidad de marcos." + "\n")
        arcpy.AddMessage("Generando Marcos Aleatorios..")
        # outName = 'PuntosA.shp'
        # arcpy.CreateRandomPoints_management(rutasalida, outName, ShapefileCorte, "", num_mr, valesc)
        # arcpy.MakeFeatureLayer_management (outpg, "grillati")
        # arcpy.SelectLayerByLocation_management("grillati", "intersect", rutasalida+"\\"+outName)
        # salidagrillap = rutasalida + "\\" + 'MarcosCS_'+namem.replace('-','')+'.shp'
        # arcpy.CopyFeatures_management("grillati", salidagrillap)
        out_points = rutasalida + "\\" + 'MarcosCS_'+namem.replace('-','')+'.shp'
        SelectRandomByCount(salidagrillain,num_mr,out_points)
        arcpy.AddMessage("Marcos de control generados")
        filet.write("Marcos de control generados" + "\n")
        # arcpy.Delete_management("grillati")
        # arcpy.Delete_management(rutasalida+"\\"+outName)
    arcpy.Delete_management(salidatb)
    filet.close()
################ Validación Tablas GDB##############################
GeodatabaseEntrada=arcpy.GetParameterAsText(0)
#Xml=sys.argv[6]
arcpy.env.overwriteOutput=True;
ruta = GeodatabaseEntrada.split("\\")
rnew = ruta[:-1]
sep = "\\"
rutasalida = sep.join(rnew)
namem = ruta[-1].split('.')[0]
filet = open(rutasalida+"\\"+"Report_"+namem+".txt","a")
filet.write("-----REPORTE DE ANALISIS GDB CBASICA-----\n")
codeblock = """rec=0
def autoIncrement():
  global rec
  pStart = 1
  pInterval = 1|
  if (rec == 0):
    rec = pStart
  else:
    rec += pInterval
  return rec"""
def elimina_tildes(cadena):
    s = ''.join((c for c in unicodedata.normalize('NFD',unicode(cadena)) if unicodedata.category(c) != 'Mn'))
    return s.decode()
def findindex(table,fieldname):
    return [i.name for i in arcpy.ListFields(table)].index(fieldname)
def repetido(featureclass):
    field_names = [i.name for i in arcpy.ListFields(featureclass) if 'Identif' in i.name]
    for field in field_names:
        #arcpy.AddMessage(field)
        tablerepetido = rutasalida + "\\repetido.dbf"
        arcpy.Statistics_analysis(featureclass, tablerepetido, [[field, "COUNT"]], field)
        #field_names_1 = ['BIdentif', 'COUNT_BIde']
        cursor = arcpy.da.SearchCursor(tablerepetido, '*')
        for row in cursor:
            identifi = row[1]
            count = row[3]
            if (count >= 2):
                filet.write('En el Featureclass ' + featureclass +' el elemento con identificador: '+ str(identifi) +' se encuentra '+ str(count) + ' veces' + "\n")
                arcpy.AddMessage('En el Featureclass ' + featureclass +' el elemento con identificador: '+ str(identifi) +' se encuentra '+ str(count) + ' veces')
                
            #if len(identifi) != 13:
            #    filet.write('En el Featureclass ' + featureclass +' el elemento con identificador: '+ str(identifi) +' tiene un numero erroneo de digitos' + "\n")
            #    arcpy.AddMessage('En el Featureclass ' + featureclass +' el elemento con identificador: '+ str(identifi) +' tiene un numero erroneo de digitos')
            
def vacios(featureclass):
    field_names = [i.name for i in arcpy.ListFields(featureclass) if i.type != 'OID']
    rows = arcpy.da.SearchCursor(featureclass, field_names)
    for row in rows:
        identifi = row[2]
        #arcpy.AddMessage('Esta es el dato: ' + str(row))
        for i in range(0, len(row)):
            #arcpy.AddMessage(row[i])
            if row[i] == 'Null' or row[i]=='NULO' or row[i]=='Nulo' or row[i]=='nulo' or row[i]=='' or row[i]=='NULL' or row[i]=='null' or row[i]==str('None') or row[i]=='None':
                filet.write('En el Featureclass ' + featureclass +' hay elementos con campos vacios '+ "\n")
                arcpy.AddMessage('En el Featureclass ' + featureclass +' hay elementos con campos vacios ')
            #arcpy.AddMessage('Esta es la fila: ' + str(row))
  
def conse_field(featureclass):
    list_conse_field = []
    list_conse_field_14 = []
    field_names = [i.name for i in arcpy.ListFields(featureclass) if 'Identif' in i.name]
    rows = arcpy.da.SearchCursor(featureclass, field_names)
    for row in rows:
        identifi = row[0]
        longitud_identifi = len(identifi)
        #arcpy.AddMessage('La longitud es: ' + str(longitud_identifi))
        if longitud_identifi == 13:
            consecutivo = identifi[-4:-2]
            #arcpy.AddMessage('El consecutivo es:' + str(consecutivo))
            list_conse_field.append(consecutivo)
        elif longitud_identifi == 14:
            consecutivo = identifi[-5:-2]
            list_conse_field_14.append(consecutivo)
            #arcpy.AddMessage('El consecutivo es:' + str(consecutivo))
        else:
            arcpy.AddMessage('El identificador tiene un numero de caracteres diferente al permitido, por favor revisar el featuclass ' + featureclass )
    list_conse_field_14.sort()            
    list_conse_field.sort()
    #arcpy.AddMessage(list_conse_field)
    z = 0
    for num in list_conse_field_14[1:]:
        #arcpy.AddMessage(int(num))
        if (int(list_conse_field_14[z]) + int(1)) == int(num):
            ''
        else:
            arcpy.AddMessage('Se debe revisar el consecutivo del campo identificador del feature class: '+ featureclass)
            filet.write('Se debe revisar el consecutivo del campo identificador del feature class: '+ featureclass + "\n")
        
        z = z + 1
    x = 0
    for num in list_conse_field[1:]:
        #arcpy.AddMessage(int(num))
        if (int(list_conse_field[x]) + int(1)) == int(num):
            ''
        else:
            arcpy.AddMessage('Se debe revisar el consecutivo del campo identificador del feature class: ' + featureclass)
            filet.write('Se debe revisar el consecutivo del campo identificador del feature class: ' + featureclass + "\n")
        
        x = x + 1
    #arcpy.AddMessage(list_conse_field)
    
        
            
            
#####################
#arcpy.FeatureClassToFeatureClass_conversion(ShapefileCorte,GeodatabaseEntrada + "\\Indice_Mapas","CORTE" )
#CORTE = ShapefileCorte
arcpy.AddMessage("Analizando Geodatabase")
arcpy.env.workspace = GeodatabaseEntrada
datasetList = arcpy.ListDatasets()
for dataset in datasetList:
    if(dataset!="IndiceMapas" and dataset!="OrdenamientoTerritorial"):
        filet.write("\n")
        arcpy.AddMessage('--------Analizando Dataset ' + dataset + '---------')
        filet.write('------------------------Analizando Dataset '+dataset + '------------------------' + "\n")
        arcpy.env.workspace = GeodatabaseEntrada + "\\" + dataset
        if(dataset=="CoberturaTierra"):
            fcList = arcpy.ListFeatureClasses()
            for fc in fcList:
                vacios(fc)
                repetido(fc)
                
                result = int(arcpy.GetCount_management(fc).getOutput(0))
                try:
                    if result>0:
                        conse_field(fc)
                        aliasn = arcpy.Describe(fc).aliasName
                        filet.write("\n \n")
                        arcpy.AddMessage('Analizando FeatureClass '+fc)
                        filet.write('Analizando FeatureClass '+fc + "\n")
                        field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                        cursor = arcpy.da.SearchCursor(fc, field_names)
                        i = 0
                        for field_name in field_names:
                            if field_name == 'RuleID':
                                index_RuleID = findindex(fc,field_name)-1
                        for row in cursor:
                            ruleid = row[index_RuleID]
                            if(ruleid!=1):
                                arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado ruleid, el valor diligenciado es: '+str(ruleid))
                                filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                i+=1
                            
                            
                        arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                        filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                    else:
                        arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                        filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                except Exception as ex:
                    arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="Elevacion"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            
                            
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'CNTipo':
                                    index_CNTipo = findindex(fc,field_name)-1
                                elif field_name == 'LDTTipo':
                                    index_LDTTipo = findindex(fc,field_name)-1
                                elif field_name == 'LDTFuente':
                                    index_LDTFuente = findindex(fc,field_name)-1
                         
                                
                                
                            #arcpy.AddMessage('En el Featureclass' + fc+ ' el campo '+ field_name + 'el indice es ' + str(index_RuleID))
                            #index_RuleID_1 = index_RuleID
                            for row in cursor:
                                if(fc=='CNivel'):
                                    ruleid = row[index_RuleID]
                                    #ruleid = row[5]
                                    tipo = row[index_CNTipo]
                                    
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' los campos RuleId y Tipo no coinciden, el valor diligenciado es, Tipo:'+str(tipo)+', RuleId: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' los campos RuleId y Tipo no coinciden, el valor diligenciado es, Tipo:'+str(tipo)+', RuleId: '+str(ruleid) + "\n")
                                        i+=1
                                else:
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_LDTTipo]
                                    fuente = row[index_LDTFuente]
                                    if(ruleid!=None and (tipo==None or fuente==None)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' los campos Tipo o Fuente no estan diligenciados, el valor de RuleId es, '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' los campos Tipo o Fuente no estan diligenciados, el valor de RuleId es, '+str(ruleid) + "\n")
                                        i+=1
                                    else:
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el valor de RuleId esta vacio')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el valor de RuleId esta vacio' + "\n")
                                        i+=1
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="Hidrografia"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'DATipo':
                                    index_DATipo = findindex(fc,field_name)-1
                                elif field_name == 'DEstado':
                                    index_DEstado = findindex(fc,field_name)-1
                                elif field_name == 'DDisperso':
                                    index_DDisperso = findindex(fc,field_name)-1
                                elif field_name == 'DNombre':
                                    index_DNombre = findindex(fc,field_name)-1    
                            for row in cursor:
                                if(fc=='BArena'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid)+ "\n")
                                        i+=1
                                elif(fc=='DAgua_P'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_DATipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='DAgua_R'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_DATipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='Drenaj_L'):
                                    ruleid = row[index_RuleID]
                                    estado = row[index_DEstado]
                                    disperso = row[index_DDisperso]
                                    nombre = row[index_DNombre]
                                    if(estado==1 and disperso=='2' and ruleid!=3):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid) + "\n")
                                        i+=1
                                    elif(estado==1 and disperso=='2' and (nombre=='' or nombre==None)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo Nombre esta vacio.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo Nombre esta vacio.' + "\n")
                                        i+=1
                                    elif(estado==1 and disperso=='1' and ruleid!=4):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid) + "\n")
                                        i+=1
                                    elif(estado==2 and disperso=='2' and ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid) + "\n")
                                        i+=1
                                    elif(estado==2 and disperso=='1' and ruleid!=2):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo RuleId esta mal diligenciado, los valores son, estado: '+str(estado) + ', Ddisperso: '+ str(disperso)+' y ruleid es: '+str(ruleid) + "\n")
                                        i+=1
                                    elif((nombre=='' or nombre==None) and estado==1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo Estado esta mal diligenciado, ya que debe ser Intermitente (2) los valores son, estado: '+str(estado) + ', Nombre: '+ str(nombre))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', el campo Estado esta mal diligenciado, ya que debe ser Intermitente (2) los valores son, estado: '+str(estado) + ', Nombre: '+ str(nombre) + "\n")
                                        i+=1
                                    if(nombre=='Null' or nombre=='NULO' or nombre=='Nulo' or nombre=='nulo' or nombre=='' or nombre=='NULL' or nombre=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Nombre, se encuentra mal diligenciado, el valor diligenciado es: '+str(nombre))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Nombre, se encuentra mal diligenciado, el valor diligenciado es: '+str(nombre) + "\n")
                                        i+=1
                                    if(disperso=='Null' or disperso=='NULO' or disperso=='Nulo' or disperso=='nulo' or disperso=='' or disperso=='NULL' or disperso=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Disperso, se encuentra mal diligenciado, el valor diligenciado es: '+str(disperso))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Disperso, se encuentra mal diligenciado, el valor diligenciado es: '+str(disperso) + "\n")
                                        i+=1
                                
                                elif(fc=='DAgua_L'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_DATipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='Drenaj_R'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[2]
                                    ngeog = row[3]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                    if(ngeog=='Null' or ngeog=='NULO' or ngeog=='Nulo' or ngeog=='nulo' or ngeog==''):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Nombre_Geografico, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngeog))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Nombre_Geografico, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngeog) + "\n")
                                        i+=1
                                else:
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                            '''
                            if(fc=='Drenaj_L'):
                                arcpy.AddField_management(fc, "Nametmp", "TEXT", 200, "", "", "", "", "")
                                exp2 = '[DNombre] & "_N"'
                                arcpy.CalculateField_management(fc, "Nametmp", exp2, "VB")
                                fld_cave = 'Nametmp'
                                caves = list(set(r[0] for r in arcpy.da.SearchCursor(fc,fld_cave)))
                                tableng = rutasalida + "\\Namedrl.dbf"
                                arcpy.CreateTable_management (rutasalida, "Namedrl.dbf")
                                arcpy.AddField_management(tableng, "NameLayer", "TEXT", 200, "", "", "", "", "")
                                arcpy.AddField_management(tableng, "FREQUENCY", "LONG", 0, "", "", "", "", "")
                                arcpy.AddField_management(tableng, "COUNT", "LONG", 0, "", "", "", "", "")
                                arcpy.AddMessage('Analizando Repeticion de Nombres de Drenajes...')
                                for cave in caves:
                                    where = '"{0}" = \'{1}\''.format(fld_cave, cave)    
                                    caveObj = arcpy.MakeFeatureLayer_management(fc, "cave", where)
                                    caven = elimina_tildes(cave)
                                    outFS = os.path.join(rutasalida, caven + '.dbf')
                                    arcpy.Statistics_analysis(caveObj, outFS , [["Nametmp", "COUNT"]])
                                    arcpy.AddField_management(outFS, "NameLayer", "TEXT", 200, "", "", "", "", "")
                                    exp2 = '"'+cave+'"'
                                    arcpy.CalculateField_management(outFS, "NameLayer", exp2, "PYTHON_9.3")
                                    arcpy.Append_management(outFS, tableng, "NO_TEST","","")
                                    arcpy.Delete_management("cave")
                                    arcpy.Delete_management(outFS)
                                field_names2 = [j.name for j in arcpy.ListFields(tableng) if j.type != 'OID']
                                cursor2 = arcpy.da.SearchCursor(tableng, field_names2)
                                for row2 in cursor2:
                                    name = row2[1].split('_')[0]
                                    name = 'Null' if name=='' else name
                                    frec = row2[2]
                                    if frec > 1:
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con nombre: '+name+', se encuentra repetido, '+str(frec)+ ' veces.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con nombre: '+name+', se encuentra repetido, '+str(frec)+ ' veces.' + "\n")
                                        i+=1
                                arcpy.DeleteField_management(fc, ["Nametmp"])
                                arcpy.Delete_management(tableng)'''
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="Geodesia"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'MRTNomencl':
                                    index_MRTNomencl = findindex(fc,field_name)-1
                            for row in cursor:
                                ruleid = row[index_RuleID]
                                nomencl = row[index_MRTNomencl]
                                if(ruleid==None):
                                    arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                    filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                    i+=1
                                if(nomencl=='Null' or nomencl=='NULO' or nomencl=='Nulo' or nomencl=='nulo' or nomencl=='' or nomencl=='NULL' or nomencl=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Nomenclatura, se encuentra mal diligenciado, el valor diligenciado es: '+str(nomencl))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Nomenclatura, se encuentra mal diligenciado, el valor diligenciado es: '+str(nomencl) + "\n")
                                        i+=1
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="InfraestructuraServicios"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'PDTipo':
                                    index_PDTipo = findindex(fc,field_name)-1
                                elif field_name == 'TubTipo':
                                    index_TubTipo = findindex(fc,field_name)-1
                            for row in cursor:
                                if(fc=='PDistr'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_PDTipo]
                                    if((ruleid == 2 and tipo == 2) or (ruleid == 3 and tipo == 3) or (ruleid == 1 and tipo == 2) or (ruleid == 1 and tipo == 2)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='RATens'):
                                    ruleid = row[index_RuleID]
                                    #if(ruleid!=1):
                                    if(ruleid not in (1,1)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='TSPubl'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid != 1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1    
                                elif(fc=='Pozo'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid != 1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1                                                                 
                                elif(fc=='Tuberi'):
                                    ruleid = row[index_RuleID]
                                    Tubtipo = row[index_TubTipo]
                                    if(ruleid != 1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1      
                                    if(Tubtipo > 5):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado TubTipo, el valor diligenciado es: '+str(Tubtipo))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado TubTipo, el valor diligenciado es: '+str(Tubtipo) + "\n")
                                        i+=1                                              
                                else:
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=2):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="NombresGeograficos"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'NGNPrincip':
                                    index_NGNPrincip = findindex(fc,field_name)-1
                                elif field_name == 'NGNAlterno':
                                    index_NGNAlterno = findindex(fc,field_name)-1
                                elif field_name == 'NGCategori':
                                    index_NGCategori = findindex(fc,field_name)-1
                                elif field_name == 'NGIdioma':
                                    index_NGIdioma = findindex(fc,field_name)-1
                                elif field_name == 'NGFuente':
                                    index_NGFuente = findindex(fc,field_name)-1
                                elif field_name == 'NGEMaxima':
                                    index_NGEMaxima = findindex(fc,field_name)-1
                                elif field_name == 'NGEMinima':
                                    index_NGEMinima = findindex(fc,field_name)-1
                                elif field_name == 'NGIORelaci':
                                    index_NGIORelaci = findindex(fc,field_name)-1
                                
                            for row in cursor:
                                ruleid = row[index_RuleID]
                                ngnpri = row[index_NGNPrincip]
                                ngnalt = row[index_NGNAlterno]
                                categoria = row[index_NGCategori]
                                ngnid = row[index_NGIdioma]
                                ngnfuente = row[index_NGFuente]
                                ngnmax = row[index_NGEMaxima]
                                ngnmin = row[index_NGEMinima]
                                ngnrelac = row[index_NGIORelaci]
                                if(ruleid!=categoria):
                                    arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Categoria y RuleId son diferentes, los valores son: '+str(categoria) + ', '+ str(ruleid)+' respectivamente.')
                                    filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Categoria y RuleId son diferentes, los valores son: '+str(categoria) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                    i+=1
                                if(ngnpri=='Null' or ngnpri=='NULO' or ngnpri=='Nulo' or ngnpri=='nulo' or ngnpri=='' or ngnpri=='NULL' or ngnpri=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNPrincip, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnpri))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNPrincip, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnpri) + "\n")
                                        i+=1
                                if(ngnalt=='Null' or ngnalt=='NULO' or ngnalt=='Nulo' or ngnalt=='nulo' or ngnalt=='' or ngnalt=='NULL' or ngnalt=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNAlterno, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnalt))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNAlterno, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnalt) + "\n")
                                        i+=1
                                if(ngnid=='Null' or ngnid=='NULO' or ngnid=='Nulo' or ngnid=='nulo' or ngnid=='' or ngnid=='NULL' or ngnid=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNIdioma, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNIdioma, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnid) + "\n")
                                        i+=1
                                if(ngnfuente=='Null' or ngnfuente=='NULO' or ngnfuente=='Nulo' or ngnfuente=='nulo' or ngnfuente=='' or ngnfuente=='NULL' or ngnfuente=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNFuente, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnfuente))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNFuente, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnfuente) + "\n")
                                        i+=1
                                if(ngnmax=='Null' or ngnmax=='NULO' or ngnmax=='Nulo' or ngnmax=='nulo' or ngnmax=='' or ngnmax=='NULL' or ngnmax=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNMaxima, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnmax))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNMaxima, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnmax) + "\n")
                                        i+=1
                                if(ngnmin=='Null' or ngnmin=='NULO' or ngnmin=='Nulo' or ngnmin=='nulo' or ngnmin=='' or ngnmin=='NULL' or ngnmin=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNMinima, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnmin))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNMinima, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnmin) + "\n")
                                        i+=1
                                if(ngnrelac=='Null' or ngnrelac=='NULO' or ngnrelac=='Nulo' or ngnrelac=='nulo' or ngnrelac=='' or ngnrelac=='NULL' or ngnrelac=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNRelac, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnrelac))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo NGNRelac, se encuentra mal diligenciado, el valor diligenciado es: '+str(ngnrelac) + "\n")
                                        i+=1
                            '''
                            arcpy.AddField_management(fc, "ConcNgnc", "TEXT", 200, "", "", "", "", "")
                            exp3 = '[NGNPrincip] & "_" & [NGCategori]'
                            arcpy.CalculateField_management(fc, "ConcNgnc", exp3, "VB")
                            fld_cave2 = 'ConcNgnc'
                            caves2 = list(set(r[0] for r in arcpy.da.SearchCursor(fc,fld_cave2)))
                            tableng2 = rutasalida + "\\Ngeog.dbf"
                            arcpy.CreateTable_management (rutasalida, "Ngeog.dbf")
                            arcpy.AddField_management(tableng2, "NameLayer", "TEXT", 200, "", "", "", "", "")
                            arcpy.AddField_management(tableng2, "FREQUENCY", "LONG", 0, "", "", "", "", "")
                            arcpy.AddField_management(tableng2, "COUNT", "LONG", 0, "", "", "", "", "")
                            arcpy.AddMessage('Analizando Repeticion de Nombres y Categorias de NG...')
                            for cave in caves2:
                                where = '"{0}" = \'{1}\''.format(fld_cave2, cave)    
                                caveObj = arcpy.MakeFeatureLayer_management(fc, "cave", where)
                                caven = elimina_tildes(cave)
                                outFS = os.path.join(rutasalida, caven + '.dbf')
                                arcpy.Statistics_analysis(caveObj, outFS , [["ConcNgnc", "COUNT"]])
                                arcpy.AddField_management(outFS, "NameLayer", "TEXT", 200, "", "", "", "", "")
                                exp2 = '"'+cave+'"'
                                arcpy.CalculateField_management(outFS, "NameLayer", exp2, "PYTHON_9.3")
                                arcpy.Append_management(outFS, tableng2, "NO_TEST","","")
                                arcpy.Delete_management("cave")
                                arcpy.Delete_management(outFS)
                            field_names2 = [j.name for j in arcpy.ListFields(tableng2) if j.type != 'OID']
                            cursor2 = arcpy.da.SearchCursor(tableng2, field_names2)
                            for row2 in cursor2:
                                name = row2[1].split('_')[0]
                                cat = row2[1].split('_')[1]
                                cat = 'Null' if cat=='' else cat
                                name = 'Null' if name=='' else name
                                frec = row2[2]
                                if frec > 1:
                                    arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con nombre: '+name+', se encuentra repetido '+str(frec) +' veces, junto con la categoria, la cual es: '+str(cat))
                                    filet.write('En el Featureclass ' +fc+' el elemento con nombre: '+name+', se encuentra repetido '+str(frec) +' veces, junto con la categoria, la cual es: '+str(cat) + "\n")
                                    i+=1
                            arcpy.DeleteField_management(fc, ["ConcNgnc"])
                            arcpy.Delete_management(tableng2) '''
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="Transporte"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'PuFuncion':
                                    index_PuFuncion = findindex(fc,field_name)-1
                                elif field_name == 'VTipo':
                                    index_VTipo = findindex(fc,field_name)-1 
                                elif field_name == 'VEstado':
                                    index_VEstado = findindex(fc,field_name)-1 
                                elif field_name == 'VCarril':
                                    index_VCarril = findindex(fc,field_name)-1 
                                elif field_name == 'VAcceso':
                                    index_VAcceso = findindex(fc,field_name)-1 
                                elif field_name == 'VFTipo':
                                    index_VFTipo = findindex(fc,field_name)-1 
                                elif field_name == 'LVTipo':
                                    index_LVTipo = findindex(fc,field_name)-1 
                            for row in cursor:
                                if(fc=='Puente_P'):
                                    ruleid = row[index_RuleID]
                                    funcion = row[index_PuFuncion]
                                    if(ruleid!=funcion):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Funcion y RuleId son diferentes, los valores son: '+str(funcion) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Funcion y RuleId son diferentes, los valores son: '+str(funcion) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='Puente_L'):
                                    ruleid = row[index_RuleID]
                                    funcion = row[index_PuFuncion]
                                    if(ruleid!=funcion):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Funcion y RuleId son diferentes, los valores son: '+str(funcion) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Funcion y RuleId son diferentes, los valores son: '+str(funcion) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='Via'):
                                    #arcpy.AddMessage('En el Featureclass ' +str(row[0]) +' '+ str(row[1]) +' '+str(row[2]) +' '+str(row[3]) +' '+str(row[4]) +' '+str(row[5]) +' '+str(row[6]) +' '+str(row[7]) +' '+str(row[8]))
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_VTipo]
                                    estado = row[index_VEstado]
                                    carril = row[index_VCarril]
                                    acceso = row[index_VAcceso]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                    if tipo==1 and (int(estado) not in (1,1) or int(carril) not in (1,1) or int(acceso) not in (1,1)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Primaria, Estado: Pavimentada, Carril:Carretera de 2, Acceso: Permanente')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Primaria, Estado: Pavimentada, Carril:Carretera de 2, Acceso: Permanente' + "\n")
                                        i+=1
                                    if tipo==2 and (int(estado) not in (1,2) or int(carril) not in (2,2) or int(acceso) not in (1,1)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Secundaria, Estado: Pavimentada o Sin Pavimentar, Carril: Carretera angosta, Acceso: Permanente')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Secundaria, Estado: Pavimentada o Sin Pavimentar, Carril: Carretera angosta, Acceso: Permanente' + "\n")
                                        i+=1
                                    if tipo==3 and (int(estado) not in (2,3) or int(carril) not in (0,0) or int(acceso) not in (2,2)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Terciaria, Estado: Sin Pavimentar o Sin Afirmado, Carril: Sin Valor, Acceso: Temporal')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Terciaria, Estado: Sin Pavimentar o Sin Afirmado, Carril: Sin Valor, Acceso: Temporal' + "\n")
                                        i+=1
                                    if tipo==4 and (int(estado) not in (4,4) or int(carril) not in (0,0) or int(acceso) not in (2,2)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Placa Huella, Estado: En Construccion, Carril: Sin Valor, Acceso: Temporal')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Placa Huella, Estado: En Construccion, Carril: Sin Valor, Acceso: Temporal' + "\n")
                                        i+=1
                                    elif tipo==5 and (int(estado) not in (0,0) or int(carril) not in (0,0) or int(acceso) not in (0,0)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Camino-Sendero, Estado: Sin Valor, Carril: Sin Valor, Acceso: Sin Valor')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Camino-Sendero, Estado: Sin Valor, Carril: Sin Valor, Acceso: Sin Valor' + "\n")
                                        i+=1
                                    elif tipo==6 and (int(estado) not in (0,0) or int(carril) not in (0,0) or int(acceso) not in (0,0)):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Peatonal, Estado: Sin Valor, Carril: Sin Valor, Acceso: Sin Valor' + estado)
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Via-Peatonal, Estado: Sin Valor, Carril: Sin Valor, Acceso: Sin Valor' + "\n")
                                        i+=1
                                    #else:
                                    #    arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO tiene diligenciado el campo Tipo')
                                    #    filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO tiene diligenciado el campo Tipo' + "\n")
                                    #    i+=1
                                elif(fc=='VFerre'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_VFTipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='LVia'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_LVTipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='Tunel'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='SVial'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='Ciclor'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='Telefe'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
        if(dataset=="ViviendaCiudadTerritorio"):
                fcList = arcpy.ListFeatureClasses()
                for fc in fcList:
                    repetido(fc)
                    vacios(fc)
                    result = int(arcpy.GetCount_management(fc).getOutput(0))
                    try:
                        if result>0:
                            conse_field(fc)
                            aliasn = arcpy.Describe(fc).aliasName
                            filet.write("\n \n")
                            arcpy.AddMessage('Analizando FeatureClass '+fc)
                            filet.write('Analizando FeatureClass '+fc + "\n")
                            field_names = [i.name for i in arcpy.ListFields(fc) if i.type != 'OID']
                            cursor = arcpy.da.SearchCursor(fc, field_names)
                            i=0
                            for field_name in field_names:
                                if field_name == 'RuleID':
                                    index_RuleID = findindex(fc,field_name)-1
                                elif field_name == 'CTipo':
                                    index_CTipo = findindex(fc,field_name)-1
                                elif field_name == 'CIdentif':
                                    index_CIdentif = findindex(fc,field_name)-1
                                elif field_name == 'CCategor':
                                    index_CCategor = findindex(fc,field_name)-1
                                elif field_name == 'CDescrip':
                                    index_CDescrip = findindex(fc,field_name)-1
                                elif field_name == 'CeTipo':
                                    index_CeTipo = findindex(fc,field_name)-1
                                elif field_name == 'MuTipo':
                                    index_MuTipo = findindex(fc,field_name)-1
                                
                            for row in cursor:
                                
                                if(fc=='Constr_P'):
                                    #arcpy.AddMessage(str(row[0]) + ' ' +str(row[1]) + ' ' +str(row[2]) + ' ' +str(row[3]) + ' ' + str(row[4]) + ' ' + str(row[5]))
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_CTipo]
                                    identif = row[index_CIdentif]
                                    categoria = row[index_CCategor]
                                    descripcion = row[index_CDescrip]
                                    if(identif=='Null' or identif=='NULO' or identif=='Nulo' or identif=='nulo' or identif=='' or identif=='NULL' or identif=='null' or identif==str('None')):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' contiene elementos con campo identificador vacio')
                                        filet.write('En el Featureclass ' +fc+' contiene elementos con campo identificador vacio' + "\n")
                                        i+=1         
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1                                     
                                    elif ((categoria == 8 or categoria == 9 or categoria == 10 or categoria == 11 or categoria == 12 or categoria == 13 or categoria == 14 or categoria == 15 or categoria == 16) and (tipo==2)):
                                        arcpy.AddMessage('')
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: No Convencional, Categoria: "Agropecuario", "Enramada, cobertizo o caney", "Galpón y gallinero", "Establo y pesebrera", "Cochera, marranera y porqueriza", "Tanque", "Secadero", "Minero", "Cementerio o parque cementerio" u " Otra construcción".')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: No Convencional, Categoria: "Agropecuario", "Enramada, cobertizo o caney", "Galpón y gallinero", "Establo y pesebrera", "Cochera, marranera y porqueriza", "Tanque", "Secadero", "Minero", "Cementerio o parque cementerio" u " Otra construcción".' + "\n")
                                        i+=1
                                    elif ((categoria == 1 or categoria == 2 or categoria == 3 or categoria == 4 or categoria == 5 or categoria == 6 or categoria == 7) and (tipo==1)):
                                        arcpy.AddMessage('')
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Convencional, Categoria: "Residencial", "Comercial", "Industrial", "Educativo", "Institucional", "Recreacional" o "Religioso". u " Otra construcción".')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO cumple la condicion de Tipo: Convencional, Categoria: "Residencial", "Comercial", "Industrial", "Educativo", "Institucional", "Recreacional" o "Religioso". u " Otra construcción".' + "\n")
                                        i+=1
                                    elif(tipo=='Null' or tipo=='NULO' or tipo=='Nulo' or tipo=='nulo' or tipo=='' or tipo=='NULL' or tipo=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO tiene diligenciado el campo Tipo')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', NO tiene diligenciado el campo Tipo' + "\n")
                                        i+=1
                                    if(descripcion=='Null' or descripcion=='NULO' or descripcion=='Nulo' or descripcion=='nulo' or descripcion==''):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Descripcion, se encuentra mal diligenciado, el valor diligenciado es: '+str(descripcion))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Descripcion, se encuentra mal diligenciado, el valor diligenciado es: '+str(descripcion) + "\n")
                                        i+=1
                                elif(fc=='Cerca'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_CeTipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                elif(fc=='Muro'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[index_MuTipo]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='Piscin'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='ZDura'):
                                    ruleid = row[index_RuleID]
                                    tipo = row[2]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                                elif(fc=='Constr_R'):
                                    ruleid = row[index_RuleID]
                                    descripcion = row[index_CDescrip]
                                    tipo = row[index_CTipo]
                                    if(ruleid!=tipo):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.')
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+', los campos Tipo y RuleId son diferentes, los valores son: '+str(tipo) + ', '+ str(ruleid)+' respectivamente.' + "\n")
                                        i+=1
                                    if(descripcion=='Null' or descripcion=='NULO' or descripcion=='Nulo' or descripcion=='nulo' or descripcion=='' or descripcion=='NULL' or descripcion=='null'):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Descripcion, se encuentra mal diligenciado, el valor diligenciado es: '+str(descripcion))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' el campo Descripcion, se encuentra mal diligenciado, el valor diligenciado es: '+str(descripcion) + "\n")
                                        i+=1
                                elif(fc=='Terrap'):
                                    ruleid = row[index_RuleID]
                                    if(ruleid!=1):
                                        arcpy.AddMessage('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid))
                                        filet.write('En el Featureclass ' +fc+' el elemento con identificador: '+row[1]+' se encuentra mal diligenciado el Ruleid, el valor diligenciado es: '+str(ruleid) + "\n")
                                        i+=1
                            arcpy.AddMessage('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i))
                            filet.write('En el Featureclass ' +fc+' el numero de errores encontrados son: '+ str(i) + "\n")
                        else:
                            arcpy.AddMessage('El FeatureClass '+fc +' se encuentra vacio')
                            filet.write('El FeatureClass '+fc +' se encuentra vacio' + "\n")
                    except Exception as ex:
                        arcpy.AddMessage("Error..."+ex.message)
arcpy.AddMessage('Analisis Terminado...Revisar el reporte TXT')
filet.write("\n \n")
filet.write('Analisis Terminado.\n')
filet.close()
##############Verificación de la conectividad de los drenajes sencillos####################################
def getworkspacedatset(dtaset):
 try:
    ndataset=""
    wsp=""
    lruta=dtaset.split(os.sep)
    ndataset= lruta[len(lruta)-1]
    wsp=dtaset.replace(os.sep+ndataset,"")
    return wsp, ndataset
 except:
     import traceback
     arcpy.AddError(traceback.format_exc())
def VerificarDrenajeEnds(dstCAgua,gdb):
  try:
    arcpy.AddMessage("---Verificando conectividad de los drenajes---")
    drSencillo= dstCAgua+ os.sep+ "Drenaj_L"
    tempdrenaje=gdbOut+os.sep+"temp_dreneje"
    ptdrenaje=gdbOut+os.sep+"puntos_drenaje"
    out_Pol="Poligonos"
    rutaPol=gdb + os.sep+out_Pol
    out_Linea="Linea"
    rutaLinea=gdb + os.sep+out_Linea
    puntoerease=gdb + os.sep+"puntos_earease"
    lypterase=gdb + os.sep+"Ly_puntos_earease"
    ptintermedios=gdb + os.sep+"Puntos_intermedios"
    intputosdr=gdb + os.sep+"Int_puntos_dr"
    lypuntos=gdb + os.sep+"ly_Int_puntos_dr"
    lypuntosdef=gdb + os.sep+"ly_puntos_def"
    puntosdef=gdb + os.sep+"Puntos_revision"
    if arcpy.Exists(tempdrenaje )== True:
            arcpy.Delete_management(tempdrenaje)
    if arcpy.Exists(ptdrenaje)== True:
            arcpy.Delete_management(ptdrenaje)
    if arcpy.Exists(rutaLinea)== True:
            arcpy.Delete_management(rutaLinea)
    if arcpy.Exists(rutaPol)== True:
            arcpy.Delete_management(rutaPol)
    if arcpy.Exists(puntoerease)== True:
            arcpy.Delete_management(puntoerease)
    if arcpy.Exists(lypterase)== True:
            arcpy.Delete_management(lypterase)
    if arcpy.Exists(ptintermedios)== True:
            arcpy.Delete_management(ptintermedios)
    if arcpy.Exists(intputosdr)== True:
            arcpy.Delete_management(intputosdr)
    if arcpy.Exists(lypuntos)== True:
            arcpy.Delete_management(lypuntos)
    if arcpy.Exists(lypuntosdef)== True:
            arcpy.Delete_management(lypuntosdef)
    if arcpy.Exists(puntosdef)== True:
            arcpy.Delete_management(puntosdef)
    if arcpy.Exists(drSencillo)== True:
      arcpy.AddMessage("-----Generamdo vertices---")
      arcpy.CopyFeatures_management(drSencillo, tempdrenaje)
      arcpy.AddField_management(tempdrenaje,"IDDREN","LONG")
      exp= "!OBJECTID!"
      arcpy.CalculateField_management(tempdrenaje, "IDDREN", exp, "PYTHON_9.3")
      arcpy.FeatureVerticesToPoints_management(tempdrenaje, ptdrenaje, "END")
      arcpy.AddMessage("-----Generando Layer linea y poligono intermedios---")
      spr=arcpy.Describe(dstCAgua).spatialReference
      arcpy.CreateFeatureclass_management(gdb, out_Pol, "POLYGON","","","",spr)
      arcpy.CreateFeatureclass_management(gdb, out_Linea, "POLYLINE","","","",spr)
      ws,dtset = getworkspacedatset(dstCAgua)
      arcpy.env.workspace =ws
      fcListPol = arcpy.ListFeatureClasses("*","polygon",dtset)
      fcListLine=arcpy.ListFeatureClasses("*","polyline",dtset)
      for fcPol in fcListPol:
        if arcpy.Exists(fcPol)== True:
           nelementos=int(arcpy.GetCount_management(fcPol).getOutput(0))
           if nelementos>0 :
              arcpy.Append_management([fcPol], rutaPol,"NO_TEST")
      for fcLine in fcListLine:
        if arcpy.Exists(fcLine)== True:
           nelementos=int(arcpy.GetCount_management(fcLine).getOutput(0))
           descf= arcpy.Describe(fcLine)
           if nelementos>0 and descf.name != "Drenaj_L" :
              arcpy.Append_management([fcLine], rutaLinea,"NO_TEST")
      arcpy.AddMessage("-----seleccionando vertices---")
      arcpy.Erase_analysis(ptdrenaje, rutaPol, puntoerease)
      arcpy.MakeFeatureLayer_management(puntoerease, lypterase)
      arcpy.SelectLayerByLocation_management(lypterase, "INTERSECT", rutaLinea, "", "NEW_SELECTION", "INVERT")
      arcpy.CopyFeatures_management(lypterase, ptintermedios)
      if int(arcpy.GetCount_management(ptintermedios).getOutput(0))>0:
        arcpy.Intersect_analysis([ptintermedios,tempdrenaje], intputosdr, "ALL")
        if gdb.find("mdb")!=-1:
         qryrev="[IDDREN]"+ " <> " +"[IDDREN_1]"
        else:
         qryrev="\"" + "IDDREN" +"\""+ " <> " +"\"" + "IDDREN_1" +"\""
        idsdr=[]
        arcpy.MakeFeatureLayer_management(intputosdr,lypuntos, qryrev)
        cursor = arcpy.SearchCursor(lypuntos)
        for row in cursor:
          iddren= row.getValue("IDDREN")
          idsdr.append(iddren)
        del cursor
        qryrev=""
        for nid in idsdr:
          if qryrev=="":
           if gdb.find("mdb")!=-1:
             qryrev="[IDDREN]"+ " NOT IN (" +str(nid)
           else:
            qryrev="\"" + "IDDREN" +"\""+ " NOT IN (" +str(nid)
          else:
           qryrev=qryrev +" , " + str(nid)
        if qryrev!= "":
         qryrev=qryrev +" )"
         arcpy.MakeFeatureLayer_management(ptintermedios, lypuntosdef,qryrev )
         arcpy.CopyFeatures_management(lypuntosdef, puntosdef)
        else:
         arcpy.AddMessage("---No se Encontraron Inconsistencias---")
    else:
        arcpy.AddMessage("---No se Encontro El Feature Class Drenaje Sencillo---")
    if arcpy.Exists(tempdrenaje )== True:
            arcpy.Delete_management(tempdrenaje)
    if arcpy.Exists(ptdrenaje)== True:
            arcpy.Delete_management(ptdrenaje)
    if arcpy.Exists(rutaLinea)== True:
            arcpy.Delete_management(rutaLinea)
    if arcpy.Exists(rutaPol)== True:
            arcpy.Delete_management(rutaPol)
    if arcpy.Exists(puntoerease)== True:
            arcpy.Delete_management(puntoerease)
    if arcpy.Exists(lypterase)== True:
            arcpy.Delete_management(lypterase)
    if arcpy.Exists(ptintermedios)== True:
            arcpy.Delete_management(ptintermedios)
    if arcpy.Exists(intputosdr)== True:
            arcpy.Delete_management(intputosdr)
    if arcpy.Exists(lypuntos)== True:
            arcpy.Delete_management(lypuntos)
    if arcpy.Exists(lypuntosdef)== True:
            arcpy.Delete_management(lypuntosdef)
  except:
     import traceback
     arcpy.AddError(traceback.format_exc())
dstCAgua=os.path.join(GeodatabaseEntrada, 'Hidrografia')
gdbOut=GeodatabaseSalida
VerificarDrenajeEnds(dstCAgua,gdbOut)
##############Verificación del sentido de los drenajes####################################
def getworkspacedatset(dtaset):
 try:
    ndataset=""
    wsp=""
    lruta=dtaset.split(os.sep)
    ndataset= lruta[len(lruta)-1]
    wsp=dtaset.replace(os.sep+ndataset,"")
    return wsp, ndataset
 except:
     import traceback
     arcpy.AddError(traceback.format_exc())
def VerificarDrenajeEnds(dstCAgua,gdb):
  try:
    arcpy.AddMessage("---Verificando direccion drenajes---")
    drSencillo= dstCAgua+ os.sep+ "Drenaj_L"
    tempdrenaje=gdbOut+os.sep+"temp_dreneje"
    ptdrenaje=gdbOut+os.sep+"puntos_drenaje"
    out_Pol="Poligonos"
    rutaPol=gdb + os.sep+out_Pol
    out_Linea="Linea"
    rutaLinea=gdb + os.sep+out_Linea
    puntoerease=gdb + os.sep+"puntos_earease"
    lypterase=gdb + os.sep+"Ly_puntos_earease"
    ptintermedios=gdb + os.sep+"Puntos_intermedios"
    intputosdr=gdb + os.sep+"Int_puntos_dr"
    lypuntos=gdb + os.sep+"ly_Int_puntos_dr"
    lypuntosdef=gdb + os.sep+"ly_puntos_def"
    puntosdef=gdb + os.sep+"Puntos_revision"
    verticesinicio=gdb + os.sep+"VerticesInicio"
    verticesinicioaltura=gdb + os.sep+"VerticesInicioaltura"
    verticesfinal=gdb + os.sep+"VerticesFinal"
    drenajesrevisar = gdb + os.sep+"drenajesrevisar"
    verticesfinalaltura=gdb + os.sep+"VerticesFinalaltura"
    dtspath = os.path.dirname(dstCAgua)
    #gdbdatos = os.chdir(dstCAgua)
    Folder = os.path.dirname(dtspath)
    CNivel = dtspath + os.sep + "Elevacion\CNivel"
    CNivelPtos = gdb + os.sep + "CNivelptos"
    TIN = Folder + os.sep + "TIN"
    DEM = gdb + os.sep+"DEM"
    ACTemp = Folder + os.sep + 'ACTemp.shp'
    AC_bufer = gdb + os.sep + "AC_bufer"
    
    if arcpy.Exists(tempdrenaje )== True:
            arcpy.Delete_management(tempdrenaje)
    if arcpy.Exists(ptdrenaje)== True:
            arcpy.Delete_management(ptdrenaje)
    if arcpy.Exists(rutaLinea)== True:
            arcpy.Delete_management(rutaLinea)
    if arcpy.Exists(rutaPol)== True:
            arcpy.Delete_management(rutaPol)
    if arcpy.Exists(puntoerease)== True:
            arcpy.Delete_management(puntoerease)
    if arcpy.Exists(lypterase)== True:
            arcpy.Delete_management(lypterase)
    if arcpy.Exists(intputosdr)== True:
            arcpy.Delete_management(intputosdr)
    if arcpy.Exists(lypuntos)== True:
            arcpy.Delete_management(lypuntos)
    if arcpy.Exists(lypuntosdef)== True:
            arcpy.Delete_management(lypuntosdef)
    if arcpy.Exists(puntosdef)== True:
            arcpy.Delete_management(puntosdef)
    result = int(arcpy.GetCount_management(CNivel).getOutput(0))
    if arcpy.Exists(drSencillo)== True and result>0:
        arcpy.AddMessage("Generando vertices iniciales de los drenajes...")
        arcpy.FeatureVerticesToPoints_management(drSencillo, verticesinicio, "START")
        arcpy.AddMessage("Generando vertices finales de los drenajes...")
        arcpy.FeatureVerticesToPoints_management(drSencillo, verticesfinal, "END")
        arcpy.AddMessage("Generando puntos a partir de la curvas de nivel...")
        arcpy.FeatureVerticesToPoints_management(CNivel, CNivelPtos, "ALL")    
        arcpy.MinimumBoundingGeometry_management(CNivel, ACTemp, "CONVEX_HULL")
        arcpy.AddMessage("Calculando el bufer del AC...")
        arcpy.Buffer_analysis(ACTemp, AC_bufer, "100 Meters")
        arcpy.AddMessage("Calculando el extent del bufer del AC...")
        arcpy.env.extent = AC_bufer
        arcpy.AddMessage("Creando Raster de alturas...")
        outIDW = Idw(CNivelPtos, "CNAltura", 10, 2, RadiusVariable(10, 150000))
        outIDW.save(Folder + os.sep + "idwout.tif")
        arcpy.AddMessage("Calculando alturas de los vertices iniciales...")
        arcpy.gp.ExtractValuesToPoints_sa(verticesinicio, outIDW, verticesinicioaltura, "INTERPOLATE", "VALUE_ONLY")
        arcpy.AddField_management(verticesinicioaltura,"Alt_ini","DOUBLE")
        arcpy.CalculateField_management(verticesinicioaltura, "Alt_ini", "[RASTERVALU]")
        arcpy.AddMessage("Calculando alturas de los vertices finales...")
        arcpy.gp.ExtractValuesToPoints_sa(verticesfinal, outIDW, verticesfinalaltura, "INTERPOLATE", "VALUE_ONLY")
        arcpy.AddField_management(verticesfinalaltura,"Alt_fin","DOUBLE")
        arcpy.CalculateField_management(verticesfinalaltura, "Alt_fin", "[RASTERVALU]")
        arcpy.AddMessage("Compilando los vertices con las alturas finales e iniciales...")
        arcpy.JoinField_management(verticesfinalaltura, "DIdentif", verticesinicioaltura, "DIdentif", "Alt_ini")
        arcpy.AddField_management(verticesfinalaltura,"Dif_Alt","DOUBLE")
        arcpy.CalculateField_management(verticesfinalaltura, "Dif_Alt", "[Alt_ini] - [Alt_fin]")
        arcpy.MakeFeatureLayer_management(drSencillo, "lyr_drSencillo")
        filet = open(Folder + os.sep +"Report_SANTANDER_QUILICHAO_2K_P2_Val.txt","a")
        fields = ['DIdentif', 'Dif_Alt']
        with arcpy.da.SearchCursor(verticesfinalaltura, fields) as cursor:
                filet.write("--- RESULTADO VALIDACIÓN SENTIDOS DE LOS DRENAJES" + " -----\n")
                for row in cursor:
                        if row[1] < 0:
                                condition = "DIdentif = '" + row[0] + "'"
                                arcpy.SelectLayerByAttribute_management("lyr_drSencillo", "ADD_TO_SELECTION", condition)
                                arcpy.AddMessage('{0}, {1}'.format(row[0], row[1]))
                                filet.write("---Se debe revisar el drenaje con el identificador: " + str(row[0]) + "tiene una diferencia de alturas negativa de: " + str(row[1]) +" -----\n")      
                                arcpy.CopyFeatures_management("lyr_drSencillo", drenajesrevisar)
        filet.close()  
    else:
        arcpy.AddMessage("---No se Encontro el Feature Class Drenaje Sencillo o el Fetaure Class de curvas de nivel esta vacio y estas son necesarias para ejecutar esta herramienta---")
    
    if arcpy.Exists(tempdrenaje )== True:
            arcpy.Delete_management(tempdrenaje)
    if arcpy.Exists(ptdrenaje)== True:
            arcpy.Delete_management(ptdrenaje)
    if arcpy.Exists(rutaLinea)== True:
            arcpy.Delete_management(rutaLinea)
    if arcpy.Exists(rutaPol)== True:
            arcpy.Delete_management(rutaPol)
    if arcpy.Exists(puntoerease)== True:
            arcpy.Delete_management(puntoerease)
    if arcpy.Exists(lypterase)== True:
            arcpy.Delete_management(lypterase)
    if arcpy.Exists(ptintermedios)== True:
            arcpy.Delete_management(ptintermedios)
    if arcpy.Exists(intputosdr)== True:
            arcpy.Delete_management(intputosdr)
    if arcpy.Exists(lypuntos)== True:
            arcpy.Delete_management(lypuntos)
    if arcpy.Exists(lypuntosdef)== True:
            arcpy.Delete_management(lypuntosdef)
    if arcpy.Exists(outIDW)== True:
            arcpy.Delete_management(outIDW)
    if arcpy.Exists(verticesinicio)== True:
            arcpy.Delete_management(verticesinicio)
    if arcpy.Exists(verticesinicioaltura)== True:
            arcpy.Delete_management(verticesinicioaltura)
    if arcpy.Exists(verticesfinal)== True:
            arcpy.Delete_management(verticesfinal)
    if arcpy.Exists(verticesfinalaltura)== True:
            arcpy.Delete_management(verticesfinalaltura)   
    if arcpy.Exists(AC_bufer)== True:
            arcpy.Delete_management(AC_bufer)   
    if arcpy.Exists(CNivelPtos)== True:
            arcpy.Delete_management(CNivelPtos)                             
    if arcpy.Exists(ACTemp)== True:
            arcpy.Delete_management(ACTemp)        
  except:
     import traceback
     #arcpy.AddError(traceback.format_exc())
VerificarDrenajeEnds(dstCAgua,gdbOut)
