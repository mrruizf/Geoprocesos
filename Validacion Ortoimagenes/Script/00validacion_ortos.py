"""
Script de consistencia conceptual y de formato para ortoimagenes de acuerdo con la resolución 471
Date: 20/07/2022
Author: Marlon Ruiz - subdirección cartográfia y geodesia
"""

import os
import arcpy
import pandas as pd

def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val == 'NO CONFORME' else 'black'
    return 'color: %s' % color

def mapearRaster(folder):
    Listaraster=[]
    for path, directories, files in os.walk(folder):
        for name in files:
            if name.endswith((".tif",".img",".sid",".jp2")):
                try:
                    Rutaraster=os.path.join(path,name)
                    Listaraster.append(Rutaraster)
                except FileNotFoundError:
                    next
    arcpy.AddWarning('Rasters dentro del directorio: '+str(len(Listaraster)))
    for i in Listaraster:
        arcpy.AddMessage(i.split('\\')[-1])
    arcpy.AddMessage('-------------')
    return Listaraster

def delimitarArea(feature,cabmpal,cenpobl):
    arcpy.AddMessage(cabmpal)
    arcpy.AddMessage(cenpobl)
    if arcpy.Exists(cabmpal)==True and arcpy.Exists(cenpobl)==True:
        #arcpy.AddMessage('ERROR AQUI')
        arcpy.management.SelectLayerByLocation(cabmpal, "INTERSECT", feature, None, "NEW_SELECTION", "NOT_INVERT")
        arcpy.conversion.FeatureClassToFeatureClass(cabmpal, arcpy.env.scratchGDB, "salida", '', '', '')
        arcpy.management.SelectLayerByLocation(cenpobl, "INTERSECT", feature, None, "NEW_SELECTION", "NOT_INVERT")
        arcpy.conversion.FeatureClassToFeatureClass(cenpobl, arcpy.env.scratchGDB, "salida1", '', '', '')
        arcpy.management.Append(arcpy.env.scratchGDB+"\\salida1", arcpy.env.scratchGDB+"\\salida", "NO_TEST", None, '', '')
    elif arcpy.Exists(cabmpal)==True:
        #arcpy.AddMessage('ERROR AQUI 2')
        arcpy.management.SelectLayerByLocation(cabmpal, "INTERSECT", feature, None, "NEW_SELECTION", "NOT_INVERT")
        arcpy.conversion.FeatureClassToFeatureClass(cabmpal, arcpy.env.scratchGDB, "salida", '', '', '')
    else:
        arcpy.AddWarning('Se toma la extensión total del proyecto para afectaciones de nubes, esto puede confundir nubes con construcciones, para mas detalle use los parametros opcionales')
    
def filtrarRaster(Listaraster,foldersalida,vfiltro,feature,cabmpal,cenpobl):
    rasterObj = arcpy.Raster(Listaraster)
    ruta = foldersalida+'\\'+Listaraster.split('\\')[-1].split('.')[0]
    arcpy.AddMessage('Generando Banda 1 para su filtrado')
    image_band_1_out = ruta +'_band_1.tif'
    arcpy.AddMessage(image_band_1_out)
    extent = rasterObj.extent
    arcpy.AddMessage('XMin: {}, YMin: {}'.format(extent.XMin, extent.YMin))
    arcpy.AddMessage('XMax: {}, YMax: {}'.format(extent.XMax, extent.YMax))
    arcpy.management.MakeRasterLayer(Listaraster, image_band_1_out, '', str(extent.XMin)+" "+str(extent.YMin)+" "+str(extent.XMax)+" "+str(extent.YMax), 1)
    arcpy.CopyRaster_management(image_band_1_out,image_band_1_out)
    banda1 = arcpy.Raster(image_band_1_out)
    arcpy.management.CreateFileGDB(foldersalida, Listaraster.split('\\')[-1].split('.')[0])
    delimitarArea(feature,cabmpal,cenpobl)
    ######################################################################
    #Filtro para nubes
    filtim = banda1 > vfiltro
    arcpy.AddMessage('Filtrando nubes para su cuantificacion')
    attExtract = arcpy.sa.ExtractByAttributes(filtim, "VALUE = 1")
    salidanub = foldersalida+'\\'+Listaraster.split('\\')[-1].split('.')[0]+'.gdb'+'\\polnubes_'+Listaraster.split('\\')[-1].split('.')[0]
    if arcpy.Exists(arcpy.env.scratchGDB+"\\salida"):
        arcpy.conversion.RasterToPolygon(attExtract, arcpy.env.scratchGDB+"\\salidanub" , "NO_SIMPLIFY","VALUE")
        arcpy.analysis.Erase(arcpy.env.scratchGDB+"\\salidanub", arcpy.env.scratchGDB+"\\salida",salidanub , None)
        #arcpy.management.Delete(arcpy.env.scratchGDB)
    else:
        arcpy.conversion.RasterToPolygon(attExtract, salidanub , "NO_SIMPLIFY","VALUE")
    ######################################################################
    #Filtro para áreas omitidas
    filtim2 = banda1 < 1
    arcpy.AddMessage('Filtrando áreas omitidas para su cuantificacion')
    attExtract2 = arcpy.sa.ExtractByAttributes(filtim2, "VALUE =1")
    salidanodata = foldersalida+'\\'+Listaraster.split('\\')[-1].split('.')[0]+'.gdb'+'\\polomitida_'+Listaraster.split('\\')[-1].split('.')[0]
    salidanodataf = foldersalida+'\\'+Listaraster.split('\\')[-1].split('.')[0]+'.gdb'+'\\polomitidadef_'+Listaraster.split('\\')[-1].split('.')[0]
    arcpy.conversion.RasterToPolygon(attExtract2, salidanodata, "NO_SIMPLIFY","VALUE")
    arcpy.analysis.Intersect([salidanodata , feature],salidanodataf , "ONLY_FID", None, "INPUT")
    #arcpy.analysis.Erase(arcpy.env.scratchGDB+"\\salidaom", feature,salidanodata , None)
    
def validarRaster(raster,respectral,rradiom,respacial,namesysreference):
    if respectral >= 3:
        comres = 'La imagen: ' + raster + ' posee ' + str(respectral) + ' bandas, por lo tanto SI cumple con la resolucion espectral'
        comres1 = 'CUMPLE'
        arcpy.AddMessage(comres)
    else:
        comres = 'La imagen: ' + raster + ' posee ' + str(respectral) + ' bandas, por lo tanto NO cumple con la resolucion espectral'
        comres1 = 'NO CUMPLE'
        arcpy.AddWarning(comres)
    num = int(rradiom[1:])
    if num >= 8:
        comrad = 'La imagen: ' + raster + ' posee una resolucion radiometrica de ' + str(rradiom) + ' bits, por lo tanto SI cumple con la resolucion radiometrica'
        comrad1 = 'CUMPLE'
        arcpy.AddMessage(comrad)
    else:
        conrad = 'La imagen: ' + raster + ' posee ' + str(rradiom) + ' bits, por lo tanto NO cumple con la resolucion radiometrica'
        comrad1 = 'NO CUMPLE'
        arcpy.AddWarning(conrad)
    escalav = escala/100
    respcm = float(respacial*100)
    if mescala == True:
        if respcm <= escalav:
            comesc = 'La imagen: ' + raster + ' posee un GSD de ' + str(respcm) + ' cm, por lo tanto SI cumple con la resolucion espacial para la escala indicada de: ' + str(escala)
            comesc1 = 'CUMPLE'
            arcpy.AddMessage(comesc)
        else:
            comesc = 'La imagen: ' + raster + ' posee un GSD de ' + str(respcm) + ' cm, por lo tanto NO cumple con la resolucion espacial para la escala indicada de: ' + str(escala)
            comesc1 = 'NO CUMPLE'
            arcpy.AddWarning(comesc)
    else:
        comesc = 'Las escalas no son las mismas para las imagenes seleccionadas'
        comesc1 = 'NO APLICA'
    if namesysreference == "MAGNA-SIRGAS / Origen-Nacional":
        conref = 'La imagen: ' + raster + ' posee el sistema de referencia ' + namesysreference+ ', por lo tanto SI cumple con el sistema de referencia.'
        conref1 = 'CUMPLE'
        arcpy.AddMessage(conref)
    else:
        conref = 'La imagen: ' + raster + ' posee el sistema de referencia ' + namesysreference+ ', por lo tanto NO cumple con el sistema de referencia.'
        conref1 = 'NO CUMPLE'
        arcpy.AddWarning(conref)
        conref = conref + '\nEl SRC correcto debe ser: MAGNA-SIRGAS / Origen-Nacional, consultar la URL: '+str('https://origen.igac.gov.co/herramientas.html')+' y descargar el prj de este recurso'
        arcpy.AddWarning('\nEl SRC correcto debe ser: MAGNA-SIRGAS / Origen-Nacional, consultar la URL: '+str('https://origen.igac.gov.co/herramientas.html')+' y descargar el prj de este recurso')
    return comres,comres1,comrad,comrad1,comesc,comesc1,conref,conref1

def reportarRaster(Listaraster):
    limagen = []
    lrespectral = []
    lcrespectral = []
    lcrespectral1 = []
    lrradiom = []
    lcrradiom = []
    lcrradiom1 = []
    lrespacial = []
    lcrespacial = []
    lcrespacial1 = []
    lsysreference = []
    lcsysreference = []
    lcsysreference1 = []
    for i in Listaraster:
        rasterObj = arcpy.Raster(i)
        respectral = rasterObj.bandCount
        rradiom = rasterObj.pixelType
        respacial = rasterObj.meanCellWidth
        sysreference = rasterObj.spatialReference.exportToString()
        namesysreference = rasterObj.spatialReference.name
        fil = rasterObj.width
        col = rasterObj.height
        area = (fil * col) * respacial**2
        arcpy.AddMessage('\nValidando Imagen')
        arcpy.AddMessage('Área total de la imagen: '+str(area)+' m² o '+str(area/10000)+' Has')
        comres,comres1,comrad,comrad1,comesc,comesc1,conref,conref1 = validarRaster(str(i),respectral,rradiom,respacial,namesysreference)
        limagen.append(i.split('\\')[-1])
        lrespectral.append(str(respectral)+' Bandas') #espectral
        lcrespectral.append(comres)
        lcrespectral1.append(comres1)
        lrradiom.append(str(rradiom[1:])+' bits') #radiometrica
        lcrradiom.append(comrad)
        lcrradiom1.append(comrad1)
        lrespacial.append(str(respacial)+' metros') #espacial
        lcrespacial.append(comesc)
        lcrespacial1.append(comesc1)
        lsysreference.append(namesysreference) #sistema de referencia
        lcsysreference.append(conref)
        lcsysreference1.append(conref1)
    dic = {'Imagen':limagen,'Res. Espacial':lrespacial,'Observación Re':lcrespacial,'Conforme/No conforme Re':lcrespacial1,'Res. Espectral':lrespectral,'Observación Rb':lcrespectral,'Conforme/No conforme Rb':lcrespectral1,'Res. Radiométrica':lrradiom,'Observación Rr':lcrradiom,'Conforme/No conforme Rr':lcrradiom1,'Sistema de Referencia':lsysreference,'Observación Src':lcsysreference,'Conforme/No conforme Src':lcsysreference1}
    df = pd.DataFrame(dic)
    df = df.style.set_properties(**{'background-color': '#FFA533','font-size': '11pt',})
    #df = df.T
    df.to_excel(foldersalida+"\Reporte_Consistencia_Orto.xlsx", sheet_name='Reporte Validación')

try:
    #Agregando los parametros para ejecución
    folder = arcpy.GetParameterAsText(0)
    feature = arcpy.GetParameterAsText(1)
    cabmpal = arcpy.GetParameterAsText(2)
    cenpobl = arcpy.GetParameterAsText(3)
    vfiltro = arcpy.GetParameter(4)
    escala = arcpy.GetParameter(5)
    escala = float(escala)
    mescala = arcpy.GetParameter(6) #¿misma escala, cuando se tienen varias imágenes?, valor bool
    foldersalida = arcpy.GetParameterAsText(7)
    #Mapeando el directorio
    Listaraster = mapearRaster(folder)
    #Validando los valores
    if len(Listaraster)>1:
        reporte = reportarRaster(Listaraster)
    elif len(Listaraster)==1:
        vfiltro = int(vfiltro)
        reporte = reportarRaster(Listaraster)
        arcpy.AddMessage('/************************************************/')
        arcpy.AddMessage('/************************************************/')
        arcpy.AddMessage('/**************Generando el filtrado*************/')
        arcpy.AddMessage('/************************************************/')
        arcpy.AddMessage('/************************************************/')
        filtrarRaster(str(Listaraster[0]),foldersalida,vfiltro,feature,cabmpal,cenpobl)
except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    arcpy.AddError(u"Error de Arcpy (Verificar el licenciamiento del conjunto de herramientas Spatial Analyst):\n {}".format(msgs))
    pass
