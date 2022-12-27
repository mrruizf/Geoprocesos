import os
import sys
import arcpy

def validando(dem,carpeta,valor,suaviza,tolerancia):
    if arcpy.Exists(arcpy.Raster(dem)):
        arcpy.AddMessage("Raster verificado correctamente")
    if arcpy.Exists(carpeta+os.sep+os.path.basename(dem).replace(".tif","")+"_Dreanajes.shp")==False and arcpy.Exists(carpeta+"/"+os.path.basename(dem).replace(".tif","")+"_Curvas.shp")==False:
        arcpy.AddMessage("Directorio de salida verificado correctamente, no existen los archivos dentro de este")
    else:
        arcpy.AddError("Ya existen los resultados del Scrip asociados a este DEM dentro de la carpeta de trabajo")
        sys.exit()
    if int(valor)>0:
        arcpy.AddMessage("El valor del ND asociado es positivo")
    else:
        arcpy.AddError("El valor asociado al ND debe ser positivo!!")
        sys.exit()
    if suaviza=="true":
        if ((tolerancia is not None or tolerancia !='') and float(tolerancia)>0):
            arcpy.AddMessage("Se puede realiar el suavizamiento de las curvas y drenajes dado que se tiene un valor de tolerancia")
        else:
            arcpy.AddError("Por favor ingrese un valor asociado a la tolerancia, recuerde que es en metros y mayor a cero\n")
            sys.exit()
    arcpy.AddMessage("***VALIDACIÓN DE PARÁMETROS FINALIZADA***\n")
        
    
try:
    entradaDEM= sys.argv[1]
    resultadosCarpeta = sys.argv[2]
    valorCeldas = sys.argv[3]
    eliminacionSegmentos= sys.argv[4]
    suavisar = sys.argv[5]
    Tolerancia=sys.argv[6]

    validando(entradaDEM,resultadosCarpeta,valorCeldas,suavisar,Tolerancia)
    
    arcpy.env.workspace=resultadosCarpeta
    rutaDrenajes = resultadosCarpeta+os.sep+os.path.basename(entradaDEM).replace(".tif","")+"_Dreanajes.shp"
    rutaCurvas = resultadosCarpeta+"/"+os.path.basename(entradaDEM).replace(".tif","")+"_Curvas.shp"

    arcpy.AddMessage("RellenoSalida: Eliminando las pequeñas imperfecciones en los datos\n")
    RellenoSalida = arcpy.sa.Fill(entradaDEM)
    arcpy.AddMessage("Direccion de drenaje: Generando la dirección de flujo de cada celda hasta su vecino(s) con pendiente descendente\n")
    direccionDrenajes = arcpy.sa.FlowDirection(RellenoSalida, "NORMAL")
    arcpy.AddMessage("Acumulación de flujo: Flujo acumulado para cada celda, determinado por la acumulación del peso de todas las celdas que fluyen hacia cada celda de pendiente descendente\n")
    acumulacionFlujo= arcpy.sa.FlowAccumulation(direccionDrenajes, "", "FLOAT")
    arcpy.AddMessage("Reduccion de Red de Drenajes\n")
    acumulacionFlujoRestringida= arcpy.sa.SetNull(acumulacionFlujo, "1", "Value < " + valorCeldas)
    arcpy.AddMessage("Orden de la red")
    ordenDrenajes = arcpy.sa.StreamOrder(acumulacionFlujoRestringida, direccionDrenajes, "STRAHLER")
    arcpy.AddMessage("Realizando la poligonización del Raster, \nRaster a Feature Class\n")
    Drenajes=arcpy.sa.StreamToFeature(ordenDrenajes, direccionDrenajes, resultadosCarpeta+"/"+os.path.basename(entradaDEM).replace(".tif","")+"_Dreanajes.shp", "SIMPLIFY")
    arcpy.AddMessage(resultadosCarpeta+os.sep+os.path.basename(entradaDEM).replace(".tif","")+"_Dreanajes.shp")
    arcpy.AddMessage("\tCreacion de curvas de nivel\n")
    arcpy.sa.Contour(RellenoSalida, resultadosCarpeta+"/"+os.path.basename(entradaDEM).replace(".tif","")+"_Curvas.shp", "25", "0", "1")

    if eliminacionSegmentos=="true":
        #!shape.length@meters!
        arcpy.AddMessage("Eliminando Segmento, seleccionando a los de longitud mayor a 150 metros")
        arcpy.AddField_management(Drenajes,"Longitud","DOUBLE")
        arcpy.CalculateField_management(Drenajes,"Longitud","!shape.length@meters!","PYTHON")
        arcpy.MakeFeatureLayer_management(Drenajes,"BorrarDrenajes",""" "Longitud" < 150 AND "GRID_CODE"=1 """)
        arcpy.DeleteFeatures_management("BorrarDrenajes")
    if suavisar == "true":
        arcpy.AddMessage("Suavisando Curvas y Drenajes")
        arcpy.SmoothLine_cartography(rutaDrenajes,rutaDrenajes.replace(".shp","Suavisados.shp"),"PAEK", Tolerancia+" Meters", "FIXED_CLOSED_ENDPOINT", "FLAG_ERRORS")
        arcpy.SmoothLine_cartography(rutaCurvas,rutaCurvas.replace(".shp","Suavisados"),"PAEK", Tolerancia+" Meters", "FIXED_CLOSED_ENDPOINT", "FLAG_ERRORS")
except arcpy.ExecuteError as err:
    arcpy.AddError(err)
